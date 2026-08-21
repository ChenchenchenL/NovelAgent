from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import AppState, require_session
from ...application.services import project_service, quality_service
from ..schemas.quality import QualityCheckRequest, QualityReportView

router = APIRouter(tags=["Quality Reports"])


def _to_report_view(r: Any) -> QualityReportView:
    return QualityReportView(
        id=r.id,
        project_id=r.project_id,
        scene_id=r.scene_id,
        revision_id=r.revision_id,
        issues=r.issues or [],
        summary=r.summary or {},
        generated_at=r.generated_at.isoformat() if r.generated_at else "",
    )


@router.post("/api/scenes/{scene_id}/quality-check", response_model=QualityReportView)
def check_scene_quality_endpoint(
    scene_id: int,
    payload: QualityCheckRequest,
    state: AppState = Depends(require_session),
) -> QualityReportView:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        try:
            report = quality_service.check_scene_quality(
                db,
                project_id=project.id,
                scene_id=scene_id,
                text_content=payload.text_content,
                genre=payload.genre,
            )
            return _to_report_view(report)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))


@router.get("/api/scenes/{scene_id}/quality-report", response_model=QualityReportView)
def get_scene_quality_report_endpoint(
    scene_id: int,
    state: AppState = Depends(require_session),
) -> QualityReportView:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        rep = quality_service.get_latest_quality_report(db, project.id, scene_id)
        if not rep:
            raise HTTPException(status_code=404, detail="未找到该场景的质量检查报告")
        return _to_report_view(rep)


@router.get("/api/quality-reports", response_model=list[QualityReportView])
def list_quality_reports_endpoint(
    state: AppState = Depends(require_session),
) -> list[QualityReportView]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        reports = quality_service.list_project_quality_reports(db, project.id)
        return [_to_report_view(r) for r in reports]
