from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Header, Query
from fastapi.responses import StreamingResponse

from ..dependencies import AppState, require_session
from ..schemas import (
    ImportCheckpointView,
    ImportJobCreate,
    ImportJobCreateResponse,
    ImportJobView,
)
from ...application.services import import_runner, import_service, project_service

router = APIRouter(tags=["Imports"])


@router.post("/api/projects/current/import-jobs", response_model=ImportJobCreateResponse)
@router.post("/api/projects/current/import", response_model=ImportJobCreateResponse)
def create_import(
    payload: ImportJobCreate,
    state: AppState = Depends(require_session),
) -> dict[str, Any]:
    project_dir, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        job, sse_url = import_service.create_import_job(
            session=db,
            session_factory=factory,
            project_id=project.id,
            project_dir=project_dir,
            source_path=payload.source_path,
            allowed_dirs=state.authorized_dirs | state.history_dirs,
            batch_size=payload.batch_size,
            auto_extract=payload.auto_extract,
        )
        return {
            "id": job.id,
            "job_id": job.id,
            "status": job.status,
            "total_files": job.total_files,
            "total_batches": job.total_batches,
            "sse_url": sse_url,
        }


@router.get("/api/import-jobs", response_model=list[ImportJobView])
@router.get("/api/projects/current/import-jobs", response_model=list[ImportJobView])
def list_jobs(state: AppState = Depends(require_session)) -> list[dict[str, Any]]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        jobs = import_service.list_import_jobs(db, project_id=project.id)
        return [_format_job(j) for j in jobs]


@router.get("/api/import-jobs/{job_id}", response_model=ImportJobView)
def get_job(job_id: int, state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        job = import_service.get_import_job(db, job_id)
        return _format_job(job)


@router.post("/api/import-jobs/{job_id}/pause", response_model=ImportJobView)
def pause_job(job_id: int, state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        job = import_service.pause_import_job(db, job_id)
        return _format_job(job)


@router.post("/api/import-jobs/{job_id}/resume", response_model=ImportJobView)
def resume_job(job_id: int, state: AppState = Depends(require_session)) -> dict[str, Any]:
    project_dir, factory = state.require_project()
    with factory() as db:
        job = import_service.resume_import_job(db, factory, project_dir, job_id)
        return _format_job(job)


@router.post("/api/import-jobs/{job_id}/retry", response_model=ImportJobView)
def retry_job(job_id: int, state: AppState = Depends(require_session)) -> dict[str, Any]:
    project_dir, factory = state.require_project()
    with factory() as db:
        job = import_service.retry_import_job(db, factory, project_dir, job_id)
        return _format_job(job)


@router.delete("/api/import-jobs/{job_id}", response_model=ImportJobView)
def cancel_job(job_id: int, state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        job = import_service.cancel_import_job(db, job_id)
        return _format_job(job)


@router.get("/api/import-jobs/{job_id}/checkpoints", response_model=list[ImportCheckpointView])
def get_checkpoints(job_id: int, state: AppState = Depends(require_session)) -> list[dict[str, Any]]:
    _, factory = state.require_project()
    with factory() as db:
        checkpoints = import_service.list_checkpoints(db, job_id)
        return [
            {
                "id": c.id,
                "job_id": c.job_id,
                "batch_index": c.batch_index,
                "file_path": c.file_path,
                "batch_info": c.batch_info,
                "items_imported": c.items_imported,
                "status": c.status,
                "error_message": c.error_message,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in checkpoints
        ]


@router.get("/api/import-jobs/{job_id}/sse")
@router.get("/api/import-jobs/{job_id}/events")
async def stream_job_events(
    job_id: int,
    since: int = Query(default=0),
    last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
    state: AppState = Depends(require_session),
) -> StreamingResponse:
    start_seq = int(last_event_id) if last_event_id and last_event_id.isdigit() else since
    return StreamingResponse(
        import_runner.stream_import_events(job_id, since_seq=start_seq),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _format_job(j: Any) -> dict[str, Any]:
    return {
        "id": j.id,
        "project_id": j.project_id,
        "source_path": j.source_path,
        "status": j.status,
        "checkpoint": j.checkpoint,
        "total_files": j.total_files,
        "total_batches": j.total_batches,
        "batch_size": j.batch_size,
        "auto_extract": j.auto_extract,
        "started_at": j.started_at.isoformat() if j.started_at else None,
        "completed_at": j.completed_at.isoformat() if j.completed_at else None,
        "created_at": j.created_at.isoformat() if j.created_at else None,
        "error_summary": j.error_summary,
    }
