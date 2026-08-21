from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import AppState, require_session
from ...application.services import plot_service, project_service
from ..schemas.plot import (
    PlotEventCreate,
    PlotEventView,
    PlotThreadCreate,
    PlotThreadUpdate,
    PlotThreadView,
)

router = APIRouter(tags=["Plot Threads & Events"])


@router.get("/api/plot-threads", response_model=list[PlotThreadView])
def list_plot_threads_endpoint(state: AppState = Depends(require_session)) -> list[PlotThreadView]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        threads = plot_service.list_plot_threads(db, project.id)
        return [
            PlotThreadView(
                id=t.id,
                project_id=t.project_id,
                name=t.name,
                thread_type=t.thread_type,
                status=t.status,
                priority=t.priority,
                description=t.description,
                start_scene_id=t.start_scene_id,
                end_scene_id=t.end_scene_id,
                created_at=t.created_at.isoformat() if t.created_at else None,
            )
            for t in threads
        ]


@router.post("/api/plot-threads", response_model=PlotThreadView)
def create_plot_thread_endpoint(payload: PlotThreadCreate, state: AppState = Depends(require_session)) -> PlotThreadView:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        t = plot_service.create_plot_thread(
            db,
            project.id,
            payload.name,
            payload.thread_type,
            payload.priority,
            payload.description,
            payload.start_scene_id,
        )
        return PlotThreadView(
            id=t.id,
            project_id=t.project_id,
            name=t.name,
            thread_type=t.thread_type,
            status=t.status,
            priority=t.priority,
            description=t.description,
            start_scene_id=t.start_scene_id,
            end_scene_id=t.end_scene_id,
            created_at=t.created_at.isoformat() if t.created_at else None,
        )


@router.get("/api/plot-threads/{thread_id}", response_model=PlotThreadView)
def get_plot_thread_endpoint(thread_id: int, state: AppState = Depends(require_session)) -> PlotThreadView:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        try:
            t = plot_service.get_plot_thread(db, thread_id, project.id)
            return PlotThreadView(
                id=t.id,
                project_id=t.project_id,
                name=t.name,
                thread_type=t.thread_type,
                status=t.status,
                priority=t.priority,
                description=t.description,
                start_scene_id=t.start_scene_id,
                end_scene_id=t.end_scene_id,
                created_at=t.created_at.isoformat() if t.created_at else None,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))


@router.put("/api/plot-threads/{thread_id}", response_model=PlotThreadView)
def update_plot_thread_endpoint(
    thread_id: int, payload: PlotThreadUpdate, state: AppState = Depends(require_session)
) -> PlotThreadView:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        try:
            t = plot_service.update_plot_thread(
                db,
                thread_id,
                project_id=project.id,
                name=payload.name,
                thread_type=payload.thread_type,
                status=payload.status,
                priority=payload.priority,
                description=payload.description,
                start_scene_id=payload.start_scene_id,
                end_scene_id=payload.end_scene_id,
            )
            return PlotThreadView(
                id=t.id,
                project_id=t.project_id,
                name=t.name,
                thread_type=t.thread_type,
                status=t.status,
                priority=t.priority,
                description=t.description,
                start_scene_id=t.start_scene_id,
                end_scene_id=t.end_scene_id,
                created_at=t.created_at.isoformat() if t.created_at else None,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/api/plot-threads/{thread_id}")
def delete_plot_thread_endpoint(thread_id: int, state: AppState = Depends(require_session)) -> dict[str, bool]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        try:
            plot_service.delete_plot_thread(db, thread_id, project.id)
            return {"ok": True}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))


@router.get("/api/plot-threads/{thread_id}/events", response_model=list[PlotEventView])
def list_plot_thread_events_endpoint(
    thread_id: int, state: AppState = Depends(require_session)
) -> list[PlotEventView]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        try:
            plot_service.get_plot_thread(db, thread_id, project.id)
            events = plot_service.list_plot_events(db, plot_thread_id=thread_id)
            return [
                PlotEventView(
                    id=e.id,
                    plot_thread_id=e.plot_thread_id,
                    event_type=e.event_type,
                    scene_id=e.scene_id,
                    narrative_time=e.narrative_time,
                    description=e.description,
                    evidence=e.evidence,
                    confirmed=e.confirmed,
                    created_at=e.created_at.isoformat() if e.created_at else None,
                )
                for e in events
            ]
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))


@router.post("/api/plot-threads/{thread_id}/events", response_model=PlotEventView)
def create_plot_event_endpoint(
    thread_id: int, payload: PlotEventCreate, state: AppState = Depends(require_session)
) -> PlotEventView:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        try:
            e = plot_service.create_plot_event(
                db,
                thread_id,
                payload.event_type,
                payload.scene_id,
                payload.description,
                project_id=project.id,
                narrative_time=payload.narrative_time,
                evidence=payload.evidence,
                confirmed=payload.confirmed,
            )
            return PlotEventView(
                id=e.id,
                plot_thread_id=e.plot_thread_id,
                event_type=e.event_type,
                scene_id=e.scene_id,
                narrative_time=e.narrative_time,
                description=e.description,
                evidence=e.evidence,
                confirmed=e.confirmed,
                created_at=e.created_at.isoformat() if e.created_at else None,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
