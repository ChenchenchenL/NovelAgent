from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import AsyncIterator
import httpx
from sqlalchemy import delete, select
from sqlalchemy.orm import sessionmaker

from ...domain.models import GenerationRun, GenerationRunEvent, GenerationWorkspace, ModelInvocation
from ...integrations.model_gateway import KeyringManager, ModelConfig, ModelGateway

logger = logging.getLogger(__name__)
active_cancel_tokens: dict[int, threading.Event] = {}
_active_tokens_lock = threading.Lock()
_event_dedupe_cache: dict[str, tuple[float, int]] = {}


def _should_emit_event(run_id: int, event_type: str, payload: dict) -> bool:
    global _event_dedupe_cache
    payload_hash = hashlib.md5(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    cache_key = f"{run_id}:{event_type}:{payload_hash}"
    now_ts = time.time()
    if cache_key in _event_dedupe_cache and now_ts - _event_dedupe_cache[cache_key][0] < 5.0:
        return False
    _event_dedupe_cache[cache_key] = (now_ts, payload.get("sequence_number", 0))
    _event_dedupe_cache = {k: v for k, v in _event_dedupe_cache.items() if now_ts - v[0] < 10.0}
    return True


def _classify_error(exc: Exception) -> tuple[str, str]:
    if isinstance(exc, httpx.TimeoutException):
        return "MODEL_TIMEOUT", "模型响应超时"
    if isinstance(exc, httpx.HTTPStatusError):
        code = exc.response.status_code
        if code == 401:
            return "AUTH_FAILED", "API Key 认证失败"
        if code == 429:
            return "RATE_LIMITED", "达到速率限制"
        return "MODEL_ERROR", f"模型服务错误：{code}"
    if isinstance(exc, httpx.ConnectError):
        return "NETWORK_ERROR", "无法连接到模型服务"
    return "MODEL_ERROR", str(exc)


def now() -> datetime:
    return datetime.now(timezone.utc)


def start_runner_thread(
    run_id: int,
    session_factory: sessionmaker,
    model_config: ModelConfig,
    invocation_id: int,
) -> threading.Event:
    cancel_token = threading.Event()
    with _active_tokens_lock:
        active_cancel_tokens[run_id] = cancel_token

    def _thread_runner():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_execute_generation_async(
                run_id=run_id,
                session_factory=session_factory,
                model_config=model_config,
                invocation_id=invocation_id,
                cancel_token=cancel_token,
            ))
        finally:
            loop.close()

    thread = threading.Thread(target=_thread_runner, daemon=True, name=f"GenRunner-{run_id}")
    thread.start()
    return cancel_token


async def _execute_generation_async(
    run_id: int,
    session_factory: sessionmaker,
    model_config: ModelConfig,
    invocation_id: int,
    cancel_token: threading.Event,
) -> None:
    seq = 2
    started = now()
    final_content = ""
    token_usage = None
    events_batch = []

    try:
        with session_factory() as db:
            run = db.get(GenerationRun, run_id)
            if not run:
                return
            run.status = "RUNNING"
            run.started_at = started
            prompt, model = run.prompt, run.actual_model
            parameters = run.request_snapshot.get("parameters", {}) if run.request_snapshot else {}
            db.add(GenerationRunEvent(
                run_id=run_id, event_type="status_change",
                payload={"run_id": run_id, "status": "RUNNING", "model": model},
                sequence_number=seq,
            ))
            db.commit()
            seq += 1

        gateway = ModelGateway(model_config)
        api_key = KeyringManager.load_key(model_config.endpoint)

        async for item in gateway.stream_chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=parameters.get("temperature", 0.7),
            max_tokens=parameters.get("max_tokens"),
            api_key=api_key,
        ):
            if cancel_token.is_set():
                break

            event_payload = None
            if item["type"] == "chunk":
                final_content = item.get("partial_content", "")
                event_payload = {
                    "token": item.get("delta", ""),
                    "index": item.get("index", 0),
                    "partial_content": final_content,
                    "sequence_number": seq,
                }
            elif item["type"] == "usage":
                token_usage = item.get("usage")
                final_content = item.get("final_content", final_content)
                event_payload = {"usage": token_usage}

            if event_payload and _should_emit_event(run_id, item["type"], event_payload):
                events_batch.append({"event_type": item["type"], "payload": event_payload, "sequence_number": seq})
                seq += 1

            if len(events_batch) >= 10:
                with session_factory() as db:
                    for evt in events_batch:
                        db.add(GenerationRunEvent(run_id=run_id, event_type=evt["event_type"], payload=evt["payload"], sequence_number=evt["sequence_number"]))
                    db.commit()
                    events_batch.clear()

        if events_batch:
            with session_factory() as db:
                for evt in events_batch:
                    db.add(GenerationRunEvent(run_id=run_id, event_type=evt["event_type"], payload=evt["payload"], sequence_number=evt["sequence_number"]))
                db.commit()
                events_batch.clear()

        if cancel_token.is_set():
            _handle_cancelled(session_factory, run_id, invocation_id, seq)
            return

        _handle_completed(session_factory, run_id, invocation_id, final_content, token_usage, started, seq)

    except Exception as exc:
        logger.exception("Generation run failed: %s", exc)
        _handle_failed(session_factory, run_id, invocation_id, exc, seq)
    finally:
        with _active_tokens_lock:
            active_cancel_tokens.pop(run_id, None)


def _handle_cancelled(session_factory: sessionmaker, run_id: int, invocation_id: int, seq: int) -> None:
    with session_factory() as db:
        run = db.get(GenerationRun, run_id)
        if run and run.status != "CANCELLED":
            run.status = "CANCELLED"
            run.completed_at = now()
            db.add(GenerationRunEvent(run_id=run_id, event_type="cancelled", payload={"run_id": run_id, "message": "任务已由用户取消"}, sequence_number=seq))
        inv = db.get(ModelInvocation, invocation_id)
        if inv:
            inv.status = "CANCELLED"
        db.commit()


def _handle_completed(
    session_factory: sessionmaker,
    run_id: int,
    invocation_id: int,
    final_content: str,
    token_usage: dict | None,
    started: datetime,
    seq: int,
) -> None:
    completed = now()
    duration = int((completed - started).total_seconds() * 1000)
    with session_factory() as db:
        run = db.get(GenerationRun, run_id)
        if run and run.status == "RUNNING":
            run.status = "COMPLETED"
            run.completed_at = completed
            run.token_usage = token_usage
            run.response_snapshot = {"content": final_content, "usage": token_usage}

            ws = db.scalar(select(GenerationWorkspace).where(GenerationWorkspace.scene_id == run.scene_id))
            if ws:
                tr = run.request_snapshot.get("target_range") if run.request_snapshot else None
                if tr and "start" in tr and "end" in tr:
                    s, e = tr["start"], tr["end"]
                    ws.draft_content = ws.draft_content[:s] + final_content + ws.draft_content[e:]
                else:
                    ws.draft_content = (ws.draft_content + "\n\n" + final_content).strip()
                ws.updated_at = completed

            db.add(GenerationRunEvent(
                run_id=run_id, event_type="success",
                payload={"run_id": run_id, "final_content": final_content, "token_usage": token_usage},
                sequence_number=seq,
            ))

        inv = db.get(ModelInvocation, invocation_id)
        if inv:
            inv.status = "COMPLETED"
            inv.token_usage = token_usage
            inv.duration_ms = duration
        db.commit()


def _handle_failed(session_factory: sessionmaker, run_id: int, invocation_id: int, exc: Exception, seq: int) -> None:
    error_code, message = _classify_error(exc)
    with session_factory() as db:
        run = db.get(GenerationRun, run_id)
        if run and run.status != "CANCELLED":
            run.status = "FAILED"
            run.error_message = f"{error_code}: {message}"
            run.completed_at = now()
            db.add(GenerationRunEvent(
                run_id=run_id, event_type="failed",
                payload={"run_id": run_id, "error_code": error_code, "message": message},
                sequence_number=seq,
            ))
        inv = db.get(ModelInvocation, invocation_id)
        if inv:
            inv.status = "FAILED"
            inv.degraded_to = f"FAILED:{error_code}"
        db.commit()


def prune_expired_events(session_factory: sessionmaker, max_age_hours: int = 24) -> int:
    """Prune generation run events older than max_age_hours (PRD D3-01)."""
    cutoff = now() - timedelta(hours=max_age_hours)
    with session_factory() as db:
        res = db.execute(delete(GenerationRunEvent).where(GenerationRunEvent.created_at < cutoff))
        db.commit()
        return res.rowcount or 0


async def stream_run_events(session_factory: sessionmaker, run_id: int, since_sequence: int = 0) -> AsyncIterator[str]:
    cursor = since_sequence
    for _ in range(100):
        with session_factory() as db:
            events = list(db.scalars(
                select(GenerationRunEvent)
                .where(GenerationRunEvent.run_id == run_id, GenerationRunEvent.sequence_number > cursor)
                .order_by(GenerationRunEvent.sequence_number.asc())
            ).all())
            run = db.get(GenerationRun, run_id)
            is_done = run.status in {"COMPLETED", "FAILED", "CANCELLED"} if run else True

        for ev in events:
            cursor = ev.sequence_number
            yield f"id: {ev.sequence_number}\nevent: {ev.event_type}\ndata: {json.dumps(ev.payload, ensure_ascii=False)}\n\n"
            if ev.event_type in {"success", "failed", "cancelled"}:
                return

        if is_done and not events:
            return

        await asyncio.sleep(0.05)
