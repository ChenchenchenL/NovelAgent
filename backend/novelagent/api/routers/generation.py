from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Header, Query
from fastapi.responses import StreamingResponse

from ..dependencies import AppState, require_session
from ..schemas import GenerateRequest, GenerationRunCreate, GenerationRunView
from ...application.services import generation_service

router = APIRouter(tags=["Generation"])


@router.post("/api/scenes/{scene_id}/generation-runs")
@router.post("/api/scenes/{scene_id}/generate")
async def create_generation_run(
    scene_id: int,
    payload: GenerationRunCreate | GenerateRequest,
    state: AppState = Depends(require_session),
) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        run, sse_url = generation_service.create_generation_run(
            session=db,
            session_factory=factory,
            scene_id=scene_id,
            payload=payload,
            model_config=state.model_config,
        )
        return {
            "id": run.id,
            "run_id": run.id,
            "status": run.status,
            "sse_url": sse_url,
        }


@router.get("/api/generation-runs/{run_id}", response_model=GenerationRunView)
def get_generation_run(run_id: int, state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        run = generation_service.get_generation_run(db, run_id)
        return {
            "id": run.id,
            "scene_id": run.scene_id,
            "task_type": run.task_type,
            "status": run.status,
            "model_tier": run.model_tier,
            "actual_model": run.actual_model,
            "token_usage": run.token_usage,
            "error_message": run.error_message,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            "created_at": run.created_at.isoformat() if run.created_at else "",
        }


@router.post("/api/generation-runs/{run_id}/cancel", response_model=GenerationRunView)
def cancel_generation_run(run_id: int, state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        run = generation_service.cancel_generation_run(db, run_id)
        return {
            "id": run.id,
            "scene_id": run.scene_id,
            "task_type": run.task_type,
            "status": run.status,
            "model_tier": run.model_tier,
            "actual_model": run.actual_model,
            "token_usage": run.token_usage,
            "error_message": run.error_message,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            "created_at": run.created_at.isoformat() if run.created_at else "",
        }


@router.get("/api/generation-runs", response_model=list[GenerationRunView])
def list_generation_runs(
    scene_id: int | None = Query(default=None),
    state: AppState = Depends(require_session),
) -> list[dict[str, Any]]:
    _, factory = state.require_project()
    with factory() as db:
        runs = generation_service.list_generation_runs(db, scene_id)
        return [
            {
                "id": r.id,
                "scene_id": r.scene_id,
                "task_type": r.task_type,
                "status": r.status,
                "model_tier": r.model_tier,
                "actual_model": r.actual_model,
                "token_usage": r.token_usage,
                "error_message": r.error_message,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                "created_at": r.created_at.isoformat() if r.created_at else "",
            }
            for r in runs
        ]


@router.get("/api/generation-runs/{run_id}/sse")
@router.get("/api/generation-runs/{run_id}/events")
async def generation_events_stream(
    run_id: int,
    since: int = Query(default=0),
    last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
    state: AppState = Depends(require_session),
) -> StreamingResponse:
    _, factory = state.require_project()
    start_seq = int(last_event_id) if last_event_id and last_event_id.isdigit() else since
    return StreamingResponse(
        generation_service.stream_run_events(factory, run_id, since_sequence=start_seq),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
