from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query

from ...application.services import community_service, project_service
from ..dependencies import AppState, require_session
from ..schemas.graphrag import (
    CommunityCreate,
    CommunityResponse,
    CommunitySummaryResponse,
    CommunityUpdate,
)

router = APIRouter(tags=["communities"])


@router.get("/api/communities", response_model=list[CommunityResponse])
def list_communities(
    community_type: str | None = Query(None),
    state: AppState = Depends(require_session),
) -> list[CommunityResponse]:
    _, factory = state.require_project()
    with factory() as db:
        proj = project_service.get_current_project(db)
        return community_service.list_communities(db, proj.id, community_type=community_type)


@router.post("/api/communities", response_model=CommunityResponse)
def create_community(
    req: CommunityCreate,
    state: AppState = Depends(require_session),
) -> CommunityResponse:
    _, factory = state.require_project()
    with factory() as db:
        proj = project_service.get_current_project(db)
        return community_service.create_community(
            db,
            project_id=proj.id,
            name=req.name,
            community_type=req.community_type,
            source_entity_type=req.source_entity_type,
            source_entity_id=req.source_entity_id,
            tags=req.tags,
        )


@router.post("/api/communities/auto-detect", response_model=list[CommunityResponse])
def auto_detect_communities(
    state: AppState = Depends(require_session),
) -> list[CommunityResponse]:
    _, factory = state.require_project()
    with factory() as db:
        proj = project_service.get_current_project(db)
        return community_service.auto_detect_and_sync_communities(db, proj.id)


@router.get("/api/communities/{id}", response_model=CommunityResponse)
def get_community(
    id: int,
    state: AppState = Depends(require_session),
) -> CommunityResponse:
    _, factory = state.require_project()
    with factory() as db:
        proj = project_service.get_current_project(db)
        try:
            return community_service.get_community(db, id, proj.id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))


@router.put("/api/communities/{id}", response_model=CommunityResponse)
def update_community(
    id: int,
    req: CommunityUpdate,
    state: AppState = Depends(require_session),
) -> CommunityResponse:
    _, factory = state.require_project()
    with factory() as db:
        proj = project_service.get_current_project(db)
        try:
            return community_service.update_community(db, id, proj.id, name=req.name, tags=req.tags, status=req.status)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/api/communities/{id}")
def delete_community(
    id: int,
    state: AppState = Depends(require_session),
) -> dict[str, str]:
    _, factory = state.require_project()
    with factory() as db:
        proj = project_service.get_current_project(db)
        try:
            community_service.delete_community(db, id, proj.id)
            return {"status": "DELETED", "id": str(id)}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))


@router.get("/api/communities/{id}/summaries", response_model=list[CommunitySummaryResponse])
def list_community_summaries(
    id: int,
    state: AppState = Depends(require_session),
) -> list[CommunitySummaryResponse]:
    _, factory = state.require_project()
    with factory() as db:
        proj = project_service.get_current_project(db)
        return community_service.list_community_summaries(db, id, proj.id)


@router.post("/api/communities/{id}/summaries/generate", response_model=CommunitySummaryResponse)
def generate_community_summary(
    id: int,
    summary_type: str = Query("OVERVIEW"),
    state: AppState = Depends(require_session),
) -> CommunitySummaryResponse:
    _, factory = state.require_project()
    with factory() as db:
        proj = project_service.get_current_project(db)
        try:
            return community_service.generate_community_summary(db, id, proj.id, summary_type=summary_type)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))


@router.post("/api/communities/{id}/summaries/rebuild", response_model=CommunitySummaryResponse)
def rebuild_community_summary(
    id: int,
    summary_type: str = Query("OVERVIEW"),
    state: AppState = Depends(require_session),
) -> CommunitySummaryResponse:
    _, factory = state.require_project()
    with factory() as db:
        proj = project_service.get_current_project(db)
        try:
            return community_service.generate_community_summary(db, id, proj.id, summary_type=summary_type)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))


@router.post("/api/communities/invalidate")
def invalidate_communities(
    entity_type: str | None = Query(None),
    entity_id: int | None = Query(None),
    state: AppState = Depends(require_session),
) -> dict[str, int]:
    _, factory = state.require_project()
    with factory() as db:
        proj = project_service.get_current_project(db)
        cnt = community_service.invalidate_affected_communities(db, proj.id, entity_type, entity_id)
        return {"invalidated_count": cnt}
