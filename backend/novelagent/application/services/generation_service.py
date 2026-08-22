from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, AsyncIterator

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from ...domain.models import Chapter, GenerationRun, GenerationRunEvent, GenerationWorkspace, ModelInvocation, Scene, SceneRevision
from ...integrations.model_gateway import ModelConfig, ModelGateway, ModelRouter
from ...integrations.prompt_templates import render_messages, render_prompt
from .generation_runner import active_cancel_tokens, start_runner_thread, stream_run_events

logger = logging.getLogger(__name__)


def now() -> datetime:
    return datetime.now(timezone.utc)


def _get_scene_content(session: Session, scene: Scene) -> str:
    if not scene.current_revision_id:
        return ""
    rev = session.get(SceneRevision, scene.current_revision_id)
    return rev.content if rev else ""


def truncate_context_to_token_budget(full_content: str, max_chars: int = 4000) -> str:
    """Keep the most relevant recent narrative context within the token budget (PRD 4.6.2)."""
    if not full_content or len(full_content) <= max_chars:
        return full_content or ""
    truncated = full_content[-max_chars:]
    first_newline = truncated.find("\n")
    if first_newline != -1 and first_newline < 120:
        truncated = truncated[first_newline + 1:]
    return truncated


def create_generation_run(
    session: Session,
    session_factory: sessionmaker,
    scene_id: int,
    payload: Any,
    model_config: ModelConfig,
) -> tuple[GenerationRun, str]:
    scene = session.get(Scene, scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="场景不存在")

    active_run = session.scalar(
        select(GenerationRun)
        .with_for_update()
        .where(
            GenerationRun.scene_id == scene_id,
            GenerationRun.status.in_(["CREATED", "PENDING", "RUNNING"]),
        )
    )
    if active_run:
        raise HTTPException(status_code=409, detail="当前场景已有正在进行的生成任务")

    task_type = getattr(payload, "task_type", "paragraph_generation") or "paragraph_generation"
    preferred_tier = getattr(payload, "tier", "T3") or "T3"
    router = ModelRouter(model_config)
    tier, model = router.route(task_type, preferred_tier)

    ws = session.scalar(select(GenerationWorkspace).where(GenerationWorkspace.scene_id == scene_id))
    full_text = ws.draft_content if ws else _get_scene_content(session, scene)
    context_text = truncate_context_to_token_budget(full_text, max_chars=3500)
    recent_text = truncate_context_to_token_budget(full_text, max_chars=800)

    prompt_context = {
        "pov": scene.pov or "主人公",
        "location": scene.location or "未定",
        "goal": scene.entry_contract.get("goal", "") if scene.entry_contract else "",
        "character_states": "当前在场角色状态正常",
        "context_text": context_text,
        "recent_text": recent_text,
        "instruction": getattr(payload, "instruction", "继续写作") or "继续写作",
    }
    rendered_prompt = render_prompt(
        task_type,
        prompt_context,
        getattr(payload, "prompt_template", None),
    )
    rendered_messages = render_messages(
        task_type,
        prompt_context,
        custom_template=getattr(payload, "prompt_template", None),
    )

    chapter = session.get(Chapter, scene.chapter_id)
    gateway = ModelGateway(model_config)
    manifest = gateway.context_manifest(
        project_id=chapter.project_id if chapter else 1,
        source_ids=[f"scene_{scene.id}"],
    )

    run = GenerationRun(
        scene_id=scene.id,
        task_type=task_type,
        status="CREATED",
        prompt=rendered_prompt,
        request_snapshot={
            "task_type": task_type,
            "tier": tier,
            "model": model,
            "messages": rendered_messages,
            "parameters": getattr(payload, "parameters", None) or {},
            "target_range": getattr(payload, "target_range", None),
        },
        model_tier=tier,
        actual_model=model,
        context_manifest=manifest,
    )
    session.add(run)
    session.flush()

    invocation = ModelInvocation(
        task_type=task_type,
        tier=tier,
        model=model,
        endpoint=model_config.endpoint,
        context_manifest=manifest,
        status="PENDING",
    )
    session.add(invocation)

    ev = GenerationRunEvent(
        run_id=run.id,
        event_type="connected",
        payload={"run_id": run.id, "status": "CREATED", "model": model, "tier": tier},
        sequence_number=1,
    )
    session.add(ev)
    session.commit()
    session.refresh(run)

    start_runner_thread(run.id, session_factory, model_config, invocation.id)
    return run, f"/api/generation-runs/{run.id}/sse"


def cancel_generation_run(session: Session, run_id: int) -> GenerationRun:
    run = session.get(GenerationRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="生成任务不存在")
    if run.status in {"COMPLETED", "FAILED", "CANCELLED"}:
        return run

    token = active_cancel_tokens.get(run_id)
    if token:
        token.set()

    run.status = "CANCELLED"
    run.completed_at = now()

    max_seq = session.scalar(
        select(GenerationRunEvent.sequence_number).where(GenerationRunEvent.run_id == run_id).order_by(GenerationRunEvent.sequence_number.desc()).limit(1)
    ) or 1
    session.add(GenerationRunEvent(
        run_id=run.id,
        event_type="cancelled",
        payload={"run_id": run.id, "message": "任务已取消"},
        sequence_number=max_seq + 1,
    ))
    session.commit()
    session.refresh(run)
    return run


def get_generation_run(session: Session, run_id: int) -> GenerationRun:
    run = session.get(GenerationRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="生成任务不存在")
    return run


def list_generation_runs(session: Session, scene_id: int | None = None) -> list[GenerationRun]:
    stmt = select(GenerationRun)
    if scene_id is not None:
        stmt = stmt.where(GenerationRun.scene_id == scene_id)
    stmt = stmt.order_by(GenerationRun.id.desc())
    return list(session.scalars(stmt).all())
