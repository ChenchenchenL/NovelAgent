from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...domain.models import GenerationWorkspace, Scene, SceneRevision
from ...domain.rules import WorkspaceUpdateData


def now() -> datetime:
    return datetime.now(timezone.utc)


def _get_scene_content(session: Session, scene: Scene) -> str:
    if not scene.current_revision_id:
        return ""
    rev = session.get(SceneRevision, scene.current_revision_id)
    return rev.content if rev else ""


def get_or_create_workspace(session: Session, scene_id: int) -> GenerationWorkspace:
    scene = session.get(Scene, scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="场景不存在")

    ws = session.scalar(select(GenerationWorkspace).where(GenerationWorkspace.scene_id == scene_id))
    if not ws:
        initial_content = _get_scene_content(session, scene)
        ws = GenerationWorkspace(
            scene_id=scene.id,
            base_revision_id=scene.current_revision_id,
            draft_content=initial_content,
            cursor_position=0,
            status="DRAFT",
        )
        session.add(ws)
        session.commit()
        session.refresh(ws)
    return ws


def update_workspace(session: Session, scene_id: int, payload: WorkspaceUpdateData | Any) -> GenerationWorkspace:
    ws = get_or_create_workspace(session, scene_id)
    if getattr(payload, "draft_content", None) is not None:
        ws.draft_content = payload.draft_content
    if getattr(payload, "cursor_position", None) is not None:
        ws.cursor_position = payload.cursor_position
    if getattr(payload, "selection_start", None) is not None:
        ws.selection_start = payload.selection_start
    if getattr(payload, "selection_end", None) is not None:
        ws.selection_end = payload.selection_end
    if getattr(payload, "undo_stack", None) is not None:
        ws.undo_stack = payload.undo_stack
    if getattr(payload, "redo_stack", None) is not None:
        ws.redo_stack = payload.redo_stack
    if getattr(payload, "auto_save_snapshot", None) is not None:
        ws.auto_save_snapshot = payload.auto_save_snapshot
    if getattr(payload, "status", None) is not None:
        ws.status = payload.status
    ws.updated_at = now()
    session.commit()
    session.refresh(ws)
    return ws


def save_snapshot(session: Session, scene_id: int) -> GenerationWorkspace:
    ws = get_or_create_workspace(session, scene_id)
    snapshot = {
        "draft_content": ws.draft_content,
        "cursor_position": ws.cursor_position,
        "selection_start": ws.selection_start,
        "selection_end": ws.selection_end,
        "timestamp": now().isoformat(),
        "base_revision_id": ws.base_revision_id,
    }
    ws.auto_save_snapshot = snapshot
    session.commit()
    session.refresh(ws)
    return ws


def restore_snapshot(session: Session, scene_id: int) -> GenerationWorkspace:
    ws = get_or_create_workspace(session, scene_id)
    if not ws.auto_save_snapshot or "draft_content" not in ws.auto_save_snapshot:
        raise HTTPException(status_code=400, detail="工作区没有可用快照")
    snap = ws.auto_save_snapshot
    ws.draft_content = snap.get("draft_content", "")
    ws.cursor_position = snap.get("cursor_position", 0)
    ws.selection_start = snap.get("selection_start")
    ws.selection_end = snap.get("selection_end")
    session.commit()
    session.refresh(ws)
    return ws


def reset_workspace(session: Session, scene_id: int) -> GenerationWorkspace:
    scene = session.get(Scene, scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="场景不存在")
    ws = get_or_create_workspace(session, scene_id)
    ws.base_revision_id = scene.current_revision_id
    ws.draft_content = _get_scene_content(session, scene)
    ws.cursor_position = 0
    ws.selection_start = None
    ws.selection_end = None
    ws.undo_stack = []
    ws.redo_stack = []
    ws.status = "DRAFT"
    session.commit()
    session.refresh(ws)
    return ws
