from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from ..dependencies import AppState, require_session
from ..schemas import WorkspaceUpdate, WorkspaceView
from ...application.services import workspace_service

router = APIRouter(tags=["Workspaces"])


@router.get("/api/scenes/{scene_id}/workspace", response_model=WorkspaceView)
def get_workspace(scene_id: int, state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        ws = workspace_service.get_or_create_workspace(db, scene_id)
        return {
            "id": ws.id,
            "scene_id": ws.scene_id,
            "base_revision_id": ws.base_revision_id,
            "draft_content": ws.draft_content,
            "cursor_position": ws.cursor_position,
            "selection_start": ws.selection_start,
            "selection_end": ws.selection_end,
            "status": ws.status,
            "auto_save_snapshot": ws.auto_save_snapshot,
            "undo_stack": ws.undo_stack or [],
            "redo_stack": ws.redo_stack or [],
            "updated_at": ws.updated_at.isoformat() if ws.updated_at else "",
        }


@router.put("/api/scenes/{scene_id}/workspace", response_model=WorkspaceView)
def update_workspace(scene_id: int, payload: WorkspaceUpdate, state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        ws = workspace_service.update_workspace(db, scene_id, payload)
        return {
            "id": ws.id,
            "scene_id": ws.scene_id,
            "base_revision_id": ws.base_revision_id,
            "draft_content": ws.draft_content,
            "cursor_position": ws.cursor_position,
            "selection_start": ws.selection_start,
            "selection_end": ws.selection_end,
            "status": ws.status,
            "auto_save_snapshot": ws.auto_save_snapshot,
            "undo_stack": ws.undo_stack or [],
            "redo_stack": ws.redo_stack or [],
            "updated_at": ws.updated_at.isoformat() if ws.updated_at else "",
        }


@router.post("/api/scenes/{scene_id}/workspace/snapshot", response_model=WorkspaceView)
def save_snapshot(scene_id: int, state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        ws = workspace_service.save_snapshot(db, scene_id)
        return {
            "id": ws.id,
            "scene_id": ws.scene_id,
            "base_revision_id": ws.base_revision_id,
            "draft_content": ws.draft_content,
            "cursor_position": ws.cursor_position,
            "selection_start": ws.selection_start,
            "selection_end": ws.selection_end,
            "status": ws.status,
            "auto_save_snapshot": ws.auto_save_snapshot,
            "undo_stack": ws.undo_stack or [],
            "redo_stack": ws.redo_stack or [],
            "updated_at": ws.updated_at.isoformat() if ws.updated_at else "",
        }


@router.post("/api/scenes/{scene_id}/workspace/restore", response_model=WorkspaceView)
def restore_snapshot(scene_id: int, state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        ws = workspace_service.restore_snapshot(db, scene_id)
        return {
            "id": ws.id,
            "scene_id": ws.scene_id,
            "base_revision_id": ws.base_revision_id,
            "draft_content": ws.draft_content,
            "cursor_position": ws.cursor_position,
            "selection_start": ws.selection_start,
            "selection_end": ws.selection_end,
            "status": ws.status,
            "auto_save_snapshot": ws.auto_save_snapshot,
            "undo_stack": ws.undo_stack or [],
            "redo_stack": ws.redo_stack or [],
            "updated_at": ws.updated_at.isoformat() if ws.updated_at else "",
        }


@router.delete("/api/scenes/{scene_id}/workspace", response_model=WorkspaceView)
def reset_workspace(scene_id: int, state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        ws = workspace_service.reset_workspace(db, scene_id)
        return {
            "id": ws.id,
            "scene_id": ws.scene_id,
            "base_revision_id": ws.base_revision_id,
            "draft_content": ws.draft_content,
            "cursor_position": ws.cursor_position,
            "selection_start": ws.selection_start,
            "selection_end": ws.selection_end,
            "status": ws.status,
            "auto_save_snapshot": ws.auto_save_snapshot,
            "undo_stack": ws.undo_stack or [],
            "redo_stack": ws.redo_stack or [],
            "updated_at": ws.updated_at.isoformat() if ws.updated_at else "",
        }
