from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import AppState, require_session
from ...application.services import project_service, summary_service
from ..schemas.search import SummaryCreateRequest, SummaryView

router = APIRouter(tags=["Summaries"])


@router.get("/api/summaries", response_model=list[SummaryView])
def list_summaries_endpoint(
    summary_type: str | None = None,
    state: AppState = Depends(require_session),
) -> list[SummaryView]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        items = summary_service.list_summaries(db, project.id, summary_type=summary_type)
        return [
            SummaryView(
                id=s.id,
                project_id=s.project_id,
                summary_type=s.summary_type,
                source_id=s.source_id,
                source_version=s.source_version,
                content=s.content,
                covered_node_ids=s.covered_node_ids or [],
                narrative_time_range=s.narrative_time_range,
            )
            for s in items
        ]


@router.get("/api/summaries/{summary_type}/{source_id}", response_model=SummaryView)
def get_summary_endpoint(
    summary_type: str,
    source_id: int,
    state: AppState = Depends(require_session),
) -> SummaryView:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        summ = summary_service.get_summary(db, project.id, summary_type, source_id)
        if not summ:
            raise HTTPException(status_code=404, detail="摘要不存在")
        return SummaryView(
            id=summ.id,
            project_id=summ.project_id,
            summary_type=summ.summary_type,
            source_id=summ.source_id,
            source_version=summ.source_version,
            content=summ.content,
            covered_node_ids=summ.covered_node_ids or [],
            narrative_time_range=summ.narrative_time_range,
        )


@router.post("/api/summaries", response_model=SummaryView)
def create_summary_endpoint(
    payload: SummaryCreateRequest,
    state: AppState = Depends(require_session),
) -> SummaryView:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        summ = summary_service.create_or_update_summary(
            db,
            project_id=project.id,
            summary_type=payload.summary_type,
            source_id=payload.source_id,
            source_version=payload.source_version,
            content=payload.content,
            covered_node_ids=payload.covered_node_ids,
            narrative_time_range=payload.narrative_time_range,
        )
        return SummaryView(
            id=summ.id,
            project_id=summ.project_id,
            summary_type=summ.summary_type,
            source_id=summ.source_id,
            source_version=summ.source_version,
            content=summ.content,
            covered_node_ids=summ.covered_node_ids or [],
            narrative_time_range=summ.narrative_time_range,
        )


@router.post("/api/summaries/rebuild")
def rebuild_summaries_endpoint(state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        count = summary_service.rebuild_summaries(db, project.id)
        return {"ok": True, "count": count}
