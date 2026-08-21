from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query

from ..dependencies import AppState, require_session
from ...application.services import fts_service, project_service, summary_service, vector_service
from ..schemas.search import FTSSearchResultItem, VectorSearchResultItem

router = APIRouter(tags=["Search & H-RAG"])


@router.get("/api/search/fts", response_model=list[FTSSearchResultItem])
def fts_search_endpoint(
    query: str = Query(..., min_length=1),
    doc_type: str | None = None,
    modality: str | None = None,
    confirmed_only: bool = False,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    state: AppState = Depends(require_session),
) -> list[FTSSearchResultItem]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        results = fts_service.search_fts(
            db,
            project_id=project.id,
            query=query,
            doc_type=doc_type,
            modality=modality,
            confirmed_only=confirmed_only,
            limit=limit,
            offset=offset,
        )
        return [
            FTSSearchResultItem(
                id=r["id"],
                project_id=r["project_id"],
                doc_type=r["doc_type"],
                source_id=r["source_id"],
                source_version=r["source_version"],
                content=r["content"],
                narrative_time=r.get("narrative_time"),
                modality=r["modality"],
                confirmed=bool(r["confirmed"]),
                score=float(r.get("score", 1.0)),
            )
            for r in results
        ]


@router.get("/api/search/vector", response_model=list[VectorSearchResultItem])
def vector_search_endpoint(
    query_text: str = Query(..., min_length=1),
    doc_type: str | None = None,
    top_k: int = Query(10, ge=1, le=100),
    min_similarity: float = Query(0.0, ge=0.0, le=1.0),
    state: AppState = Depends(require_session),
) -> list[VectorSearchResultItem]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        results = vector_service.search_vectors(
            db,
            project_id=project.id,
            query_text=query_text,
            doc_type=doc_type,
            top_k=top_k,
            min_similarity=min_similarity,
        )
        return [
            VectorSearchResultItem(
                id=r["id"],
                project_id=r["project_id"],
                doc_type=r["doc_type"],
                source_id=r["source_id"],
                source_version=r["source_version"],
                content=r["content"],
                narrative_time=r.get("narrative_time"),
                modality=r["modality"],
                confirmed=bool(r["confirmed"]),
                similarity=float(r["similarity"]),
            )
            for r in results
        ]


@router.get("/api/search/hrag")
def hrag_search_endpoint(
    scene_id: int = Query(...),
    max_tokens: int = Query(4000, ge=100, le=32000),
    include_plot_threads: bool = True,
    include_adjacent_scenes: bool = True,
    include_recent_text: bool = True,
    state: AppState = Depends(require_session),
) -> list[dict[str, Any]]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        try:
            return summary_service.hierarchical_retrieve(
                db,
                project_id=project.id,
                scene_id=scene_id,
                max_tokens=max_tokens,
                include_plot_threads=include_plot_threads,
                include_adjacent_scenes=include_adjacent_scenes,
                include_recent_text=include_recent_text,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
