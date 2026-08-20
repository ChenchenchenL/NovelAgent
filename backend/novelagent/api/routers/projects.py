from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from ..dependencies import AppState, require_session
from ..schemas import (
    ImportRequest,
    ProjectOpen,
    ProjectTreeView,
    ProjectView,
    ReorderRequest,
    VolumeCreate,
    VolumeUpdate,
    VolumeView,
)
from ...application.services import import_service, project_service

router = APIRouter(tags=["Projects"])


@router.post("/api/projects/open", response_model=ProjectView)
def open_project(payload: ProjectOpen, state: AppState = Depends(require_session)) -> dict[str, Any]:
    info, engine, factory, path = project_service.open_or_create_project(
        state.settings, state.authorized_dirs, payload.path
    )
    state.engine, state.session_factory, state.project_dir = engine, factory, path
    return info


@router.get("/api/projects/current", response_model=ProjectView)
def current_project(state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        return {"id": project.id, "name": project.name, "path": project.path}


@router.get("/api/projects/current/tree", response_model=ProjectTreeView)
def get_project_tree(state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        return project_service.build_project_tree(db, project.id)


@router.get("/api/projects/current/volumes", response_model=list[VolumeView])
def get_volumes(state: AppState = Depends(require_session)) -> list[dict[str, Any]]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        rows = project_service.list_volumes(db, project.id)
        return [
            {
                "id": v.id,
                "project_id": v.project_id,
                "title": v.title,
                "sequence": v.sequence,
                "status": v.status,
                "created_at": v.created_at.isoformat() if v.created_at else "",
            }
            for v in rows
        ]


@router.post("/api/projects/current/volumes", response_model=VolumeView)
def create_volume(payload: VolumeCreate, state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        volume = project_service.create_volume(db, project.id, payload.title, payload.status or "IDEA")
        return {
            "id": volume.id,
            "project_id": volume.project_id,
            "title": volume.title,
            "sequence": volume.sequence,
            "status": volume.status,
            "created_at": volume.created_at.isoformat() if volume.created_at else "",
        }


@router.put("/api/volumes/{volume_id}", response_model=VolumeView)
def update_volume(volume_id: int, payload: VolumeUpdate, state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        volume = project_service.update_volume(db, project.id, volume_id, payload.title, payload.status)
        return {
            "id": volume.id,
            "project_id": volume.project_id,
            "title": volume.title,
            "sequence": volume.sequence,
            "status": volume.status,
            "created_at": volume.created_at.isoformat() if volume.created_at else "",
        }


@router.delete("/api/volumes/{volume_id}")
def delete_volume(volume_id: int, state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        deleted_id = project_service.delete_volume(db, project.id, volume_id)
        return {"status": "ok", "deleted_volume_id": deleted_id}


@router.put("/api/projects/current/reorder")
def reorder(payload: ReorderRequest, state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        project_service.reorder_items(db, project.id, payload.type, payload.parent_id, payload.order)
        return {"status": "ok", "type": payload.type, "order": payload.order}


@router.post("/api/projects/current/import")
def import_project(payload: ImportRequest, state: AppState = Depends(require_session)) -> dict[str, Any]:
    project_dir, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        return import_service.run_project_import(
            db, project.id, project_dir, payload.source_path, state.authorized_dirs | state.history_dirs
        )
