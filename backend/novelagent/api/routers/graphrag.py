from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query

from ...application.services import graphrag_service, project_service
from ..dependencies import AppState, require_session
from ..schemas.graphrag import GraphRAGQueryCreate, GraphRAGQueryResponse

router = APIRouter(tags=["graphrag"])


@router.post("/api/graphrag/query", response_model=GraphRAGQueryResponse)
def execute_query(
    req: GraphRAGQueryCreate,
    state: AppState = Depends(require_session),
) -> GraphRAGQueryResponse:
    _, factory = state.require_project()
    with factory() as db:
        proj = project_service.get_current_project(db)
        return graphrag_service.execute_graphrag_query(
            db,
            project_id=proj.id,
            query_type=req.query_type,
            query_text=req.query_text,
            parameters=req.parameters,
        )


@router.get("/api/graphrag/queries", response_model=list[GraphRAGQueryResponse])
def list_queries(
    query_type: str | None = Query(None),
    state: AppState = Depends(require_session),
) -> list[GraphRAGQueryResponse]:
    _, factory = state.require_project()
    with factory() as db:
        proj = project_service.get_current_project(db)
        return graphrag_service.list_graphrag_queries(db, proj.id, query_type=query_type)


@router.get("/api/graphrag/queries/{id}", response_model=GraphRAGQueryResponse)
def get_query(
    id: int,
    state: AppState = Depends(require_session),
) -> GraphRAGQueryResponse:
    _, factory = state.require_project()
    with factory() as db:
        proj = project_service.get_current_project(db)
        try:
            return graphrag_service.get_graphrag_query(db, id, proj.id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))


@router.post("/api/graphrag/queries/{id}/retry", response_model=GraphRAGQueryResponse)
def retry_query(
    id: int,
    state: AppState = Depends(require_session),
) -> GraphRAGQueryResponse:
    _, factory = state.require_project()
    with factory() as db:
        proj = project_service.get_current_project(db)
        try:
            old_q = graphrag_service.get_graphrag_query(db, id, proj.id)
            return graphrag_service.execute_graphrag_query(
                db,
                project_id=proj.id,
                query_type=old_q.query_type,
                query_text=old_q.query_text,
                parameters=old_q.parameters,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
