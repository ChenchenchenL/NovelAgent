from __future__ import annotations

from typing import Any, Optional
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ...domain.quality_models import AuthorFeedback


def record_author_feedback(
    session: Session,
    project_id: int,
    issue_type: str,
    decision: str,
    scope: str | None = None,
    expiry_scene_id: int | None = None,
    reason: str | None = None,
    scene_id: int | None = None,
    revision_id: int | None = None,
) -> AuthorFeedback:
    feedback = AuthorFeedback(
        project_id=project_id,
        issue_type=issue_type,
        decision=decision.upper(),
        scope=scope.upper() if scope else "ONCE",
        expiry_scene_id=expiry_scene_id,
        reason=reason,
        scene_id=scene_id,
        revision_id=revision_id,
    )
    session.add(feedback)
    session.commit()
    session.refresh(feedback)
    return feedback


def list_author_feedback(
    session: Session,
    project_id: int,
    issue_type: str | None = None,
    decision: str | None = None,
) -> list[AuthorFeedback]:
    stmt = select(AuthorFeedback).where(AuthorFeedback.project_id == project_id)
    if issue_type:
        stmt = stmt.where(AuthorFeedback.issue_type == issue_type)
    if decision:
        stmt = stmt.where(AuthorFeedback.decision == decision.upper())
    stmt = stmt.order_by(AuthorFeedback.id.desc())
    return list(session.scalars(stmt).all())


def get_active_ignored_rules(
    session: Session,
    project_id: int,
    scene_id: int | None = None,
    revision_id: int | None = None,
) -> list[AuthorFeedback]:
    """Retrieve feedback records where author decided to IGNORE issues within active scope."""
    stmt = select(AuthorFeedback).where(
        AuthorFeedback.project_id == project_id,
        AuthorFeedback.decision == "IGNORE",
    )
    feedbacks = list(session.scalars(stmt).all())
    active: list[AuthorFeedback] = []

    for f in feedbacks:
        if f.scope == "ALWAYS":
            active.append(f)
        elif f.scope == "THIS_SCENE" and scene_id and f.scene_id == scene_id:
            active.append(f)
        elif f.scope == "ONCE" and scene_id and f.scene_id == scene_id:
            # ONCE applies only to the specific revision or single invocation
            if revision_id is not None and f.revision_id is not None:
                if f.revision_id == revision_id:
                    active.append(f)
            else:
                active.append(f)
        elif f.expiry_scene_id and scene_id and scene_id <= f.expiry_scene_id:
            active.append(f)
    return active


def get_feedback_statistics(session: Session, project_id: int) -> dict[str, Any]:
    feedbacks = list_author_feedback(session, project_id)
    total = len(feedbacks)
    accept_count = sum(1 for f in feedbacks if f.decision == "ACCEPT")
    reject_count = sum(1 for f in feedbacks if f.decision == "REJECT")
    ignore_count = sum(1 for f in feedbacks if f.decision == "IGNORE")

    by_type: dict[str, dict[str, int]] = {}
    for f in feedbacks:
        if f.issue_type not in by_type:
            by_type[f.issue_type] = {"total": 0, "accept": 0, "reject": 0, "ignore": 0}
        by_type[f.issue_type]["total"] += 1
        by_type[f.issue_type][f.decision.lower()] += 1

    return {
        "project_id": project_id,
        "total_feedback": total,
        "accept_count": accept_count,
        "reject_count": reject_count,
        "ignore_count": ignore_count,
        "false_positive_rate": round(ignore_count / max(1, total), 2),
        "by_issue_type": by_type,
    }
