from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from ..dependencies import AppState, get_scene_content, require_session
from ..schemas import (
    PatchCreate,
    RevisionView,
    SceneCreate,
    SceneEntryContractUpdate,
    SceneExitStateUpdate,
    SceneStatusUpdate,
    SceneUpdate,
    SceneView,
)
from ...application.services import project_service, scene_service

router = APIRouter(tags=["Scenes"])


@router.post("/api/chapters/{chapter_id}/scenes", response_model=SceneView)
def create_scene(chapter_id: int, payload: SceneCreate, state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        scene = scene_service.create_scene(
            db,
            project_id=project.id,
            chapter_id=chapter_id,
            title=payload.title,
            pov=payload.pov,
            location=payload.location,
        )
        return {
            "id": scene.id,
            "chapter_id": scene.chapter_id,
            "title": scene.title,
            "sequence": scene.sequence,
            "pov": scene.pov,
            "location": scene.location,
            "status": scene.status,
            "current_revision_id": scene.current_revision_id,
            "content": "",
            "entry_contract": scene.entry_contract,
            "exit_state": scene.exit_state,
        }


@router.get("/api/scenes/{scene_id}", response_model=SceneView)
def get_scene(scene_id: int, state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        scene = scene_service.get_scene(db, scene_id)
        return {
            "id": scene.id,
            "chapter_id": scene.chapter_id,
            "title": scene.title,
            "sequence": scene.sequence,
            "pov": scene.pov,
            "location": scene.location,
            "status": scene.status,
            "current_revision_id": scene.current_revision_id,
            "content": get_scene_content(db, scene),
            "entry_contract": scene.entry_contract,
            "exit_state": scene.exit_state,
        }


@router.put("/api/scenes/{scene_id}", response_model=SceneView)
def update_scene(scene_id: int, payload: SceneUpdate, state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        scene = scene_service.update_scene(db, scene_id, payload.title, payload.pov, payload.location)
        return {
            "id": scene.id,
            "chapter_id": scene.chapter_id,
            "title": scene.title,
            "sequence": scene.sequence,
            "pov": scene.pov,
            "location": scene.location,
            "status": scene.status,
            "current_revision_id": scene.current_revision_id,
            "content": get_scene_content(db, scene),
            "entry_contract": scene.entry_contract,
            "exit_state": scene.exit_state,
        }


@router.post("/api/scenes/{scene_id}/status")
def update_scene_status(scene_id: int, payload: SceneStatusUpdate, state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        scene = scene_service.change_scene_status(db, scene_id, payload.status)
        return {"id": scene.id, "status": scene.status}


@router.post("/api/scenes/{scene_id}/patches")
def create_patch(scene_id: int, payload: PatchCreate, state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        revision = scene_service.create_patch(
            db,
            scene_id=scene_id,
            base_revision_id=payload.base_revision_id,
            content=payload.content,
            source=payload.source,
        )
        return {"revision_id": revision.id, "status": "DRAFT"}


@router.post("/api/scenes/{scene_id}/revisions/{revision_id}/accept")
def accept_revision(scene_id: int, revision_id: int, state: AppState = Depends(require_session)) -> dict[str, Any]:
    project_dir, factory = state.require_project()
    with factory() as db:
        scene, revision = scene_service.accept_revision(db, project_dir, scene_id, revision_id)
        return {"scene_id": scene.id, "revision_id": revision.id, "status": scene.status}


@router.get("/api/scenes/{scene_id}/revisions", response_model=list[RevisionView])
def list_revisions(scene_id: int, state: AppState = Depends(require_session)) -> list[dict[str, Any]]:
    _, factory = state.require_project()
    with factory() as db:
        rows = scene_service.list_revisions(db, scene_id)
        return [
            {
                "id": r.id,
                "scene_id": r.scene_id,
                "base_revision_id": r.base_revision_id,
                "source": r.source,
                "content_hash": r.content_hash,
                "created_at": r.created_at.isoformat() if r.created_at else "",
            }
            for r in rows
        ]


@router.get("/api/scenes/{scene_id}/revisions/{revision_id}", response_model=RevisionView)
def get_revision(scene_id: int, revision_id: int, state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        r = scene_service.get_revision(db, scene_id, revision_id)
        return {
            "id": r.id,
            "scene_id": r.scene_id,
            "base_revision_id": r.base_revision_id,
            "content": r.content,
            "source": r.source,
            "content_hash": r.content_hash,
            "created_at": r.created_at.isoformat() if r.created_at else "",
        }


@router.put("/api/scenes/{scene_id}/entry-contract")
def update_entry_contract(scene_id: int, payload: SceneEntryContractUpdate, state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        scene = scene_service.update_entry_contract(db, scene_id, payload.entry_contract)
        return {"id": scene.id, "entry_contract": scene.entry_contract}


@router.put("/api/scenes/{scene_id}/exit-state")
def update_exit_state(scene_id: int, payload: SceneExitStateUpdate, state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        scene = scene_service.update_exit_state(db, scene_id, payload.exit_state)
        return {"id": scene.id, "exit_state": scene.exit_state}


@router.delete("/api/scenes/{scene_id}")
def delete_scene(scene_id: int, state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        deleted_id = scene_service.delete_scene(db, scene_id)
        return {"status": "ok", "deleted_scene_id": deleted_id}
