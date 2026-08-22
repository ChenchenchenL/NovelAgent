from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException

from ...application.services import (
    feedback_optimization_service,
    feedback_service,
    project_service,
)
from ..dependencies import AppState, require_session
from ..schemas.graphrag import FeedbackOptimizationApplyRequest

router = APIRouter(tags=["feedback_optimization"])


@router.get("/api/feedback-optimization/stats")
def get_stats(
    state: AppState = Depends(require_session),
) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        proj = project_service.get_current_project(db)
        return feedback_service.get_feedback_statistics(db, proj.id)


@router.get("/api/feedback-optimization/suggestions")
def get_suggestions(
    state: AppState = Depends(require_session),
) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        proj = project_service.get_current_project(db)
        return feedback_optimization_service.get_optimization_suggestions(db, proj.id)


@router.post("/api/feedback-optimization/apply")
def apply_suggestion(
    req: FeedbackOptimizationApplyRequest,
    state: AppState = Depends(require_session),
) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        proj = project_service.get_current_project(db)
        return feedback_optimization_service.apply_optimization_suggestion(
            db,
            project_id=proj.id,
            issue_type=req.issue_type,
            action=req.action,
            reason=req.reason,
        )
