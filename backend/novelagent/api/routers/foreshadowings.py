from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import AppState, require_session
from ...application.services import foreshadowing_service, project_service
from ..schemas.plot import (
    ForeshadowingCreate,
    ForeshadowingPayoffRequest,
    ForeshadowingUpdate,
    ForeshadowingView,
)

router = APIRouter(tags=["Foreshadowings"])


@router.get("/api/foreshadowings", response_model=list[ForeshadowingView])
def list_foreshadowings_endpoint(
    status: str | None = None,
    plot_thread_id: int | None = None,
    state: AppState = Depends(require_session),
) -> list[ForeshadowingView]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        items = foreshadowing_service.list_foreshadowings(db, project.id, status=status, plot_thread_id=plot_thread_id)
        return [
            ForeshadowingView(
                id=f.id,
                project_id=f.project_id,
                plot_thread_id=f.plot_thread_id,
                name=f.name,
                status=f.status,
                priority=f.priority,
                target_chapter_start=f.target_chapter_start,
                target_chapter_end=f.target_chapter_end,
                earliest_trigger_chapter=f.earliest_trigger_chapter,
                latest_payoff_chapter=f.latest_payoff_chapter,
                trigger_condition_type=f.trigger_condition_type,
                trigger_condition_params=f.trigger_condition_params,
                visibility=f.visibility,
                visible_to_character_id=f.visible_to_character_id,
                anchors=f.anchors or [],
                setup_scene_id=f.setup_scene_id,
                payoff_scene_id=f.payoff_scene_id,
                description=f.description,
                confirmed=f.confirmed,
                created_at=f.created_at.isoformat() if f.created_at else None,
            )
            for f in items
        ]


@router.post("/api/foreshadowings", response_model=ForeshadowingView)
def create_foreshadowing_endpoint(
    payload: ForeshadowingCreate, state: AppState = Depends(require_session)
) -> ForeshadowingView:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        try:
            f = foreshadowing_service.create_foreshadowing(
                db,
                project.id,
                name=payload.name,
                setup_scene_id=payload.setup_scene_id,
                plot_thread_id=payload.plot_thread_id,
                priority=payload.priority,
                target_chapter_start=payload.target_chapter_start,
                target_chapter_end=payload.target_chapter_end,
                earliest_trigger_chapter=payload.earliest_trigger_chapter,
                latest_payoff_chapter=payload.latest_payoff_chapter,
                trigger_condition_type=payload.trigger_condition_type,
                trigger_condition_params=payload.trigger_condition_params,
                visibility=payload.visibility,
                visible_to_character_id=payload.visible_to_character_id,
                anchors=payload.anchors,
                description=payload.description,
                confirmed=payload.confirmed,
            )
            return ForeshadowingView(
                id=f.id,
                project_id=f.project_id,
                plot_thread_id=f.plot_thread_id,
                name=f.name,
                status=f.status,
                priority=f.priority,
                target_chapter_start=f.target_chapter_start,
                target_chapter_end=f.target_chapter_end,
                earliest_trigger_chapter=f.earliest_trigger_chapter,
                latest_payoff_chapter=f.latest_payoff_chapter,
                trigger_condition_type=f.trigger_condition_type,
                trigger_condition_params=f.trigger_condition_params,
                visibility=f.visibility,
                visible_to_character_id=f.visible_to_character_id,
                anchors=f.anchors or [],
                setup_scene_id=f.setup_scene_id,
                payoff_scene_id=f.payoff_scene_id,
                description=f.description,
                confirmed=f.confirmed,
                created_at=f.created_at.isoformat() if f.created_at else None,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))


@router.get("/api/foreshadowings/{foreshadowing_id}", response_model=ForeshadowingView)
def get_foreshadowing_endpoint(foreshadowing_id: int, state: AppState = Depends(require_session)) -> ForeshadowingView:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        try:
            f = foreshadowing_service.get_foreshadowing(db, foreshadowing_id, project.id)
            return ForeshadowingView(
                id=f.id,
                project_id=f.project_id,
                plot_thread_id=f.plot_thread_id,
                name=f.name,
                status=f.status,
                priority=f.priority,
                target_chapter_start=f.target_chapter_start,
                target_chapter_end=f.target_chapter_end,
                earliest_trigger_chapter=f.earliest_trigger_chapter,
                latest_payoff_chapter=f.latest_payoff_chapter,
                trigger_condition_type=f.trigger_condition_type,
                trigger_condition_params=f.trigger_condition_params,
                visibility=f.visibility,
                visible_to_character_id=f.visible_to_character_id,
                anchors=f.anchors or [],
                setup_scene_id=f.setup_scene_id,
                payoff_scene_id=f.payoff_scene_id,
                description=f.description,
                confirmed=f.confirmed,
                created_at=f.created_at.isoformat() if f.created_at else None,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))


@router.put("/api/foreshadowings/{foreshadowing_id}", response_model=ForeshadowingView)
def update_foreshadowing_endpoint(
    foreshadowing_id: int, payload: ForeshadowingUpdate, state: AppState = Depends(require_session)
) -> ForeshadowingView:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        try:
            f = foreshadowing_service.update_foreshadowing(
                db,
                foreshadowing_id,
                project_id=project.id,
                name=payload.name,
                priority=payload.priority,
                status=payload.status,
                target_chapter_start=payload.target_chapter_start,
                target_chapter_end=payload.target_chapter_end,
                earliest_trigger_chapter=payload.earliest_trigger_chapter,
                latest_payoff_chapter=payload.latest_payoff_chapter,
                trigger_condition_type=payload.trigger_condition_type,
                trigger_condition_params=payload.trigger_condition_params,
                visibility=payload.visibility,
                visible_to_character_id=payload.visible_to_character_id,
                anchors=payload.anchors,
                description=payload.description,
            )
            return ForeshadowingView(
                id=f.id,
                project_id=f.project_id,
                plot_thread_id=f.plot_thread_id,
                name=f.name,
                status=f.status,
                priority=f.priority,
                target_chapter_start=f.target_chapter_start,
                target_chapter_end=f.target_chapter_end,
                earliest_trigger_chapter=f.earliest_trigger_chapter,
                latest_payoff_chapter=f.latest_payoff_chapter,
                trigger_condition_type=f.trigger_condition_type,
                trigger_condition_params=f.trigger_condition_params,
                visibility=f.visibility,
                visible_to_character_id=f.visible_to_character_id,
                anchors=f.anchors or [],
                setup_scene_id=f.setup_scene_id,
                payoff_scene_id=f.payoff_scene_id,
                description=f.description,
                confirmed=f.confirmed,
                created_at=f.created_at.isoformat() if f.created_at else None,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))


@router.post("/api/foreshadowings/{foreshadowing_id}/payoff", response_model=ForeshadowingView)
def payoff_foreshadowing_endpoint(
    foreshadowing_id: int, payload: ForeshadowingPayoffRequest, state: AppState = Depends(require_session)
) -> ForeshadowingView:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        try:
            f = foreshadowing_service.payoff_foreshadowing(
                db, foreshadowing_id, payload.payoff_scene_id, project_id=project.id, description=payload.description
            )
            return ForeshadowingView(
                id=f.id,
                project_id=f.project_id,
                plot_thread_id=f.plot_thread_id,
                name=f.name,
                status=f.status,
                priority=f.priority,
                target_chapter_start=f.target_chapter_start,
                target_chapter_end=f.target_chapter_end,
                earliest_trigger_chapter=f.earliest_trigger_chapter,
                latest_payoff_chapter=f.latest_payoff_chapter,
                trigger_condition_type=f.trigger_condition_type,
                trigger_condition_params=f.trigger_condition_params,
                visibility=f.visibility,
                visible_to_character_id=f.visible_to_character_id,
                anchors=f.anchors or [],
                setup_scene_id=f.setup_scene_id,
                payoff_scene_id=f.payoff_scene_id,
                description=f.description,
                confirmed=f.confirmed,
                created_at=f.created_at.isoformat() if f.created_at else None,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/api/foreshadowings/{foreshadowing_id}")
def delete_foreshadowing_endpoint(foreshadowing_id: int, state: AppState = Depends(require_session)) -> dict[str, bool]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        try:
            foreshadowing_service.delete_foreshadowing(db, foreshadowing_id, project.id)
            return {"ok": True}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))


@router.get("/api/scenes/{scene_id}/foreshadowings/scheduled")
def schedule_scene_foreshadowings_endpoint(
    scene_id: int, state: AppState = Depends(require_session)
) -> list[dict[str, Any]]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        try:
            return foreshadowing_service.schedule_foreshadowings_for_scene(db, project.id, scene_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
