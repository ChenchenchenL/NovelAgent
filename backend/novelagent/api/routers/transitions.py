from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import AppState, require_session
from ...application.services import project_service, transition_service
from ..schemas.plot import SceneContractsUpdateRequest, TransitionCheckRequest

router = APIRouter(tags=["Scene Transitions"])


@router.post("/api/scenes/{scene_id}/check-transition")
def check_scene_transition_endpoint(
    scene_id: int,
    payload: TransitionCheckRequest,
    state: AppState = Depends(require_session),
) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        try:
            return transition_service.check_scene_transition_service(
                db,
                scene_id,
                project_id=project.id,
                prev_scene_id=payload.prev_scene_id,
                entry_contract_override=payload.entry_contract_override,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))


@router.get("/api/scenes/{scene_id}/transition-report")
def get_scene_transition_report_endpoint(
    scene_id: int, state: AppState = Depends(require_session)
) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        try:
            return transition_service.check_scene_transition_service(db, scene_id, project_id=project.id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))


@router.put("/api/scenes/{scene_id}/contracts")
def update_scene_contracts_endpoint(
    scene_id: int,
    payload: SceneContractsUpdateRequest,
    state: AppState = Depends(require_session),
) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        try:
            scene = transition_service.update_scene_contracts(
                db,
                scene_id,
                project_id=project.id,
                entry_contract=payload.entry_contract,
                exit_state=payload.exit_state,
            )
            return {
                "id": scene.id,
                "entry_contract": scene.entry_contract,
                "exit_state": scene.exit_state,
            }
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
