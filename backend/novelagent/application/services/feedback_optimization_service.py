from __future__ import annotations

from typing import Any
from sqlalchemy.orm import Session

from ...domain.graphrag_rules import calculate_feedback_optimization_suggestions
from .feedback_service import get_feedback_statistics, record_author_feedback


def get_optimization_suggestions(session: Session, project_id: int) -> dict[str, Any]:
    """Generate optimization suggestions based on false-positive rates of issue types."""
    stats = get_feedback_statistics(session, project_id)
    suggestions = calculate_feedback_optimization_suggestions(stats)
    return {
        "project_id": project_id,
        "feedback_summary": stats,
        "suggestions": suggestions,
    }


def apply_optimization_suggestion(
    session: Session,
    project_id: int,
    issue_type: str,
    action: str = "SUPPRESS",
    reason: str | None = None,
) -> dict[str, Any]:
    """Apply an optimization action by creating a project-level ALWAYS ignore rule."""
    feedback = record_author_feedback(
        session,
        project_id=project_id,
        issue_type=issue_type,
        decision="IGNORE",
        scope="ALWAYS",
        reason=reason or f"自动优化规则应用: {action}",
    )
    return {
        "status": "APPLIED",
        "issue_type": issue_type,
        "scope": "ALWAYS",
        "feedback_id": feedback.id,
    }
