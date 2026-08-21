from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import AppState, require_session
from ...application.services import beat_service, project_service
from ..schemas.quality import (
    BeatAdvanceRequest,
    BeatCreate,
    BeatStopRequest,
    BeatUpdate,
    BeatView,
)

router = APIRouter(tags=["Beat Contracts"])


def _to_beat_view(b: Any) -> BeatView:
    return BeatView(
        id=b.id,
        project_id=b.project_id,
        scene_id=b.scene_id,
        generation_run_id=b.generation_run_id,
        required_advancements=b.required_advancements or [],
        stop_conditions=b.stop_conditions or [],
        target_word_count=b.target_word_count,
        max_word_count=b.max_word_count,
        forbidden_patterns=b.forbidden_patterns or [],
        status=b.status,
        advancements_achieved=b.advancements_achieved or [],
        actual_word_count=b.actual_word_count,
        created_at=b.created_at.isoformat() if b.created_at else "",
    )


@router.post("/api/scenes/{scene_id}/beats", response_model=BeatView)
def create_scene_beat(
    scene_id: int,
    payload: BeatCreate,
    state: AppState = Depends(require_session),
) -> BeatView:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        try:
            beat = beat_service.create_beat_contract(
                db,
                project_id=project.id,
                scene_id=scene_id,
                required_advancements=payload.required_advancements,
                stop_conditions=payload.stop_conditions,
                target_word_count=payload.target_word_count,
                max_word_count=payload.max_word_count,
                forbidden_patterns=payload.forbidden_patterns,
                generation_run_id=payload.generation_run_id,
            )
            return _to_beat_view(beat)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))


@router.get("/api/scenes/{scene_id}/beats", response_model=list[BeatView])
def list_scene_beats_endpoint(
    scene_id: int,
    state: AppState = Depends(require_session),
) -> list[BeatView]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        beats = beat_service.list_scene_beats(db, project.id, scene_id)
        return [_to_beat_view(b) for b in beats]


@router.get("/api/beats/{beat_id}", response_model=BeatView)
def get_beat_endpoint(
    beat_id: int,
    state: AppState = Depends(require_session),
) -> BeatView:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        try:
            b = beat_service.get_beat_contract(db, beat_id, project.id)
            return _to_beat_view(b)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))


@router.put("/api/beats/{beat_id}", response_model=BeatView)
def update_beat_endpoint(
    beat_id: int,
    payload: BeatUpdate,
    state: AppState = Depends(require_session),
) -> BeatView:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        try:
            b = beat_service.update_beat_contract(
                db,
                beat_id,
                project.id,
                required_advancements=payload.required_advancements,
                stop_conditions=payload.stop_conditions,
                target_word_count=payload.target_word_count,
                max_word_count=payload.max_word_count,
                forbidden_patterns=payload.forbidden_patterns,
            )
            return _to_beat_view(b)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))


@router.post("/api/beats/{beat_id}/advance", response_model=BeatView)
def advance_beat_endpoint(
    beat_id: int,
    payload: BeatAdvanceRequest,
    state: AppState = Depends(require_session),
) -> BeatView:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        try:
            b = beat_service.advance_beat(db, beat_id, project.id, payload.advancement)
            return _to_beat_view(b)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))


@router.post("/api/beats/{beat_id}/stop", response_model=BeatView)
def stop_beat_endpoint(
    beat_id: int,
    payload: BeatStopRequest,
    state: AppState = Depends(require_session),
) -> BeatView:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        try:
            b = beat_service.stop_beat(db, beat_id, project.id, payload.reason, payload.actual_word_count)
            return _to_beat_view(b)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
