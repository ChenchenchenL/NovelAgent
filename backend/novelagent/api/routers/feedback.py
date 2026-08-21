from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query

from ..dependencies import AppState, require_session
from ...application.services import feedback_service, project_service
from ..schemas.quality import AuthorFeedbackCreate, AuthorFeedbackView

router = APIRouter(tags=["Author Feedback"])


def _to_feedback_view(f: Any) -> AuthorFeedbackView:
    return AuthorFeedbackView(
        id=f.id,
        project_id=f.project_id,
        issue_type=f.issue_type,
        decision=f.decision,
        scope=f.scope or "ONCE",
        expiry_scene_id=f.expiry_scene_id,
        reason=f.reason,
        scene_id=f.scene_id,
        revision_id=f.revision_id,
        created_at=f.created_at.isoformat() if f.created_at else "",
    )


@router.get("/api/author-feedback", response_model=list[AuthorFeedbackView])
def list_author_feedback_endpoint(
    issue_type: str | None = None,
    decision: str | None = None,
    state: AppState = Depends(require_session),
) -> list[AuthorFeedbackView]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        items = feedback_service.list_author_feedback(db, project.id, issue_type=issue_type, decision=decision)
        return [_to_feedback_view(f) for f in items]


@router.post("/api/author-feedback", response_model=AuthorFeedbackView)
def create_author_feedback_endpoint(
    payload: AuthorFeedbackCreate,
    state: AppState = Depends(require_session),
) -> AuthorFeedbackView:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        fb = feedback_service.record_author_feedback(
            db,
            project_id=project.id,
            issue_type=payload.issue_type,
            decision=payload.decision,
            scope=payload.scope,
            expiry_scene_id=payload.expiry_scene_id,
            reason=payload.reason,
            scene_id=payload.scene_id,
            revision_id=payload.revision_id,
        )
        return _to_feedback_view(fb)


@router.get("/api/author-feedback/stats")
def get_feedback_stats_endpoint(
    state: AppState = Depends(require_session),
) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        return feedback_service.get_feedback_statistics(db, project.id)
