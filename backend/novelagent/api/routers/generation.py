from __future__ import annotations

import asyncio
from typing import Any, AsyncIterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from ..dependencies import AppState, append_event, get_app_state, require_session
from ..schemas import GenerateRequest
from ...application.services import scene_service
from ...domain.models import GenerationRun, ModelInvocation

router = APIRouter(tags=["Generation"])


@router.post("/api/scenes/{scene_id}/generate")
async def generate(scene_id: int, payload: GenerateRequest, state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        scene = scene_service.get_scene(db, scene_id)
        run = GenerationRun(scene_id=scene.id, prompt=payload.instruction, status="RUNNING")
        invocation = ModelInvocation(
            task_type="scene_generation",
            tier=payload.tier,
            model=state.model_config.models.get(payload.tier, "adapter-mock"),
            status="RUNNING",
        )
        db.add(run)
        db.add(invocation)
        db.commit()
        db.refresh(run)

    append_event(state, run.id, "started", f"Run #{run.id} started on tier {payload.tier}")

    async def _runner() -> None:
        await asyncio.sleep(0.05)
        append_event(state, run.id, "delta", "【Agent 生成片段】林舟按住剑柄，缓步推开客栈后门。")
        append_event(state, run.id, "completed", "生成完成")

    asyncio.create_task(_runner())
    return {"run_id": run.id, "status": "RUNNING"}


@router.get("/api/generation-runs/{run_id}/events")
async def generation_events(run_id: int, state: AppState = Depends(get_app_state)) -> StreamingResponse:
    async def _stream() -> AsyncIterator[str]:
        cursor = 0
        while True:
            with state.event_lock:
                current_events = list(state.events.get(run_id, []))
            while cursor < len(current_events):
                ev = current_events[cursor]
                cursor += 1
                yield f"event: {ev['event']}\ndata: {ev['data']}\n\n"
                if ev["event"] in {"completed", "failed"}:
                    return
            await asyncio.sleep(0.1)

    return StreamingResponse(_stream(), media_type="text/event-stream")
