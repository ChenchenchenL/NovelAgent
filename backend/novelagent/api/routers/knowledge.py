from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select

from ..dependencies import AppState, require_session
from ...application.services import project_service
from ...domain.models import ItemEntity, ShadowEntity

router = APIRouter(tags=["Knowledge"])


@router.get("/api/items")
def list_items(state: AppState = Depends(require_session)) -> list[dict[str, Any]]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        items = db.scalars(select(ItemEntity).where(ItemEntity.project_id == project.id)).all()
        return [{"id": i.id, "name": i.name, "current_holder": i.current_holder, "state": i.current_state} for i in items]


@router.get("/api/shadow-entities")
def list_shadow_entities(state: AppState = Depends(require_session)) -> list[dict[str, Any]]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        entities = db.scalars(select(ShadowEntity).where(ShadowEntity.project_id == project.id)).all()
        return [{"id": s.id, "name": s.display_name, "canonical": s.canonical_character} for s in entities]
