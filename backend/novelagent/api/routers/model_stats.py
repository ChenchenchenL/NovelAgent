from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query

from ...application.services import model_stats_service, project_service
from ..dependencies import AppState, require_session
from ..schemas.graphrag import ModelStatsDailyResponse, ModelStatsSummaryResponse

router = APIRouter(tags=["model_stats"])


@router.get("/api/model-stats/summary", response_model=ModelStatsSummaryResponse)
def get_summary(
    state: AppState = Depends(require_session),
) -> ModelStatsSummaryResponse:
    _, factory = state.require_project()
    with factory() as db:
        proj = project_service.get_current_project(db)
        return model_stats_service.get_model_stats_summary(db, proj.id)


@router.get("/api/model-stats/daily", response_model=list[ModelStatsDailyResponse])
def list_daily_stats(
    state: AppState = Depends(require_session),
) -> list[ModelStatsDailyResponse]:
    _, factory = state.require_project()
    with factory() as db:
        proj = project_service.get_current_project(db)
        return model_stats_service.list_model_stats_daily(db, proj.id)


@router.get("/api/model-stats/by-model")
def get_by_model_stats(
    state: AppState = Depends(require_session),
) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        proj = project_service.get_current_project(db)
        daily = model_stats_service.list_model_stats_daily(db, proj.id)
        by_model: dict[str, dict[str, Any]] = {}
        for d in daily:
            m = d.model_name
            if m not in by_model:
                by_model[m] = {"calls": 0, "tokens": 0, "cost": 0.0, "degraded": 0}
            by_model[m]["calls"] += d.total_calls
            by_model[m]["tokens"] += d.total_tokens
            by_model[m]["cost"] = round(by_model[m]["cost"] + d.estimated_cost, 4)
            by_model[m]["degraded"] += d.degraded_calls
        return by_model


@router.get("/api/model-stats/by-task")
def get_by_task_stats(
    state: AppState = Depends(require_session),
) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        proj = project_service.get_current_project(db)
        daily = model_stats_service.list_model_stats_daily(db, proj.id)
        by_task: dict[str, dict[str, Any]] = {}
        for d in daily:
            t = d.task_type
            if t not in by_task:
                by_task[t] = {"calls": 0, "tokens": 0, "cost": 0.0, "degraded": 0}
            by_task[t]["calls"] += d.total_calls
            by_task[t]["tokens"] += d.total_tokens
            by_task[t]["cost"] = round(by_task[t]["cost"] + d.estimated_cost, 4)
            by_task[t]["degraded"] += d.degraded_calls
        return by_task


@router.get("/api/model-stats/degradation")
def get_degradation_stats(
    state: AppState = Depends(require_session),
) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        proj = project_service.get_current_project(db)
        summary = model_stats_service.get_model_stats_summary(db, proj.id)
        return {
            "total_calls": summary["total_calls"],
            "degraded_calls": summary["degraded_calls"],
            "degradation_rate": summary["degradation_rate"],
        }


@router.post("/api/model-stats/aggregate", response_model=list[ModelStatsDailyResponse])
def trigger_aggregation(
    state: AppState = Depends(require_session),
) -> list[ModelStatsDailyResponse]:
    _, factory = state.require_project()
    with factory() as db:
        proj = project_service.get_current_project(db)
        return model_stats_service.aggregate_model_stats(db, proj.id)
