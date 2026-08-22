from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query

from ...application.services import global_analysis_service, project_service
from ..dependencies import AppState, require_session
from ..schemas.graphrag import GlobalAnalysisReportResponse

router = APIRouter(tags=["global_analysis"])


@router.post("/api/global-analysis/character-arcs", response_model=GlobalAnalysisReportResponse)
def analyze_character_arcs(
    state: AppState = Depends(require_session),
) -> GlobalAnalysisReportResponse:
    _, factory = state.require_project()
    with factory() as db:
        proj = project_service.get_current_project(db)
        return global_analysis_service.run_character_arcs_analysis(db, proj.id)


@router.post("/api/global-analysis/relationship-network", response_model=GlobalAnalysisReportResponse)
def analyze_relationship_network(
    state: AppState = Depends(require_session),
) -> GlobalAnalysisReportResponse:
    _, factory = state.require_project()
    with factory() as db:
        proj = project_service.get_current_project(db)
        return global_analysis_service.run_relationship_network_analysis(db, proj.id)


@router.post("/api/global-analysis/foreshadow-audit", response_model=GlobalAnalysisReportResponse)
def analyze_foreshadow_audit(
    state: AppState = Depends(require_session),
) -> GlobalAnalysisReportResponse:
    _, factory = state.require_project()
    with factory() as db:
        proj = project_service.get_current_project(db)
        return global_analysis_service.run_foreshadow_audit(db, proj.id)


@router.post("/api/global-analysis/plot-rupture", response_model=GlobalAnalysisReportResponse)
def analyze_plot_rupture(
    state: AppState = Depends(require_session),
) -> GlobalAnalysisReportResponse:
    _, factory = state.require_project()
    with factory() as db:
        proj = project_service.get_current_project(db)
        return global_analysis_service.run_plot_rupture_audit(db, proj.id)


@router.get("/api/global-analysis/reports", response_model=list[GlobalAnalysisReportResponse])
def list_reports(
    report_type: str | None = Query(None),
    state: AppState = Depends(require_session),
) -> list[GlobalAnalysisReportResponse]:
    _, factory = state.require_project()
    with factory() as db:
        proj = project_service.get_current_project(db)
        return global_analysis_service.list_global_analysis_reports(db, proj.id, report_type=report_type)


@router.get("/api/global-analysis/reports/{id}", response_model=GlobalAnalysisReportResponse)
def get_report(
    id: int,
    state: AppState = Depends(require_session),
) -> GlobalAnalysisReportResponse:
    _, factory = state.require_project()
    with factory() as db:
        proj = project_service.get_current_project(db)
        try:
            return global_analysis_service.get_global_analysis_report(db, id, proj.id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
