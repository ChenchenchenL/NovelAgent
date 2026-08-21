from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import AppState, require_session
from ...application.services import fts_service, index_orchestrator, kg_service, project_service, vector_service
from ..schemas.search import IndexRebuildResponse, IndexStatusView

router = APIRouter(tags=["Index Management"])


@router.post("/api/indexes/rebuild-all", response_model=IndexRebuildResponse)
def rebuild_all_indexes_endpoint(state: AppState = Depends(require_session)) -> IndexRebuildResponse:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        res = index_orchestrator.rebuild_all_indexes(db, project.id)
        return IndexRebuildResponse(**res)


@router.post("/api/indexes/fts/rebuild")
def rebuild_fts_endpoint(state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        count = fts_service.rebuild_fts_index(db, project.id)
        return {"ok": True, "indexed_count": count}


@router.post("/api/indexes/vector/rebuild")
def rebuild_vector_endpoint(state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        count = vector_service.rebuild_vector_index(db, project.id)
        return {"ok": True, "indexed_count": count}


@router.post("/api/indexes/kg/rebuild")
def rebuild_kg_endpoint(state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        res = kg_service.rebuild_kg_projection(db, project.id)
        return {"ok": True, **res}


@router.get("/api/indexes/status", response_model=IndexStatusView)
def get_indexes_status_endpoint(state: AppState = Depends(require_session)) -> IndexStatusView:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        data = index_orchestrator.get_all_index_statuses(db, project.id)
        return IndexStatusView(**data)


@router.post("/api/indexes/validate")
def validate_indexes_endpoint(state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        return index_orchestrator.validate_indexes(db, project.id)
