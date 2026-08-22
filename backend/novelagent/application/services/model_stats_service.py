from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ...domain.graphrag_models import ModelStatsDaily
from ...domain.models import ModelInvocation


def aggregate_model_stats(
    session: Session,
    project_id: int,
    target_date: date | None = None,
) -> list[ModelStatsDaily]:
    """Aggregate ModelInvocation logs into daily model statistics."""
    today = target_date or datetime.now(timezone.utc).date()
    invocations = list(session.scalars(select(ModelInvocation)).all())

    # Filter for this project from context_manifest if present
    filtered_invs: list[ModelInvocation] = []
    for inv in invocations:
        manifest = inv.context_manifest or {}
        p_id = manifest.get("project_id")
        if p_id is None or p_id == project_id:
            filtered_invs.append(inv)

    # Group by (model_name, task_type)
    groups: dict[tuple[str, str], list[ModelInvocation]] = {}
    for inv in filtered_invs:
        inv_date = inv.created_at.date() if inv.created_at else today
        if inv_date == today:
            key = (inv.model or "mock-model", inv.task_type or "generation")
            groups.setdefault(key, []).append(inv)

    stats_list: list[ModelStatsDaily] = []
    for (model, task), invs in groups.items():
        total = len(invs)
        success = sum(1 for i in invs if i.status == "SUCCESS")
        failed = sum(1 for i in invs if i.status == "FAILED")
        degraded = sum(1 for i in invs if i.degraded_to is not None)

        prompt_tokens = 0
        completion_tokens = 0
        total_tok = 0
        for i in invs:
            usage = i.token_usage or {}
            p_tok = usage.get("prompt_tokens", 0)
            c_tok = usage.get("completion_tokens", 0)
            t_tok = usage.get("total_tokens", p_tok + c_tok)
            prompt_tokens += p_tok
            completion_tokens += c_tok
            total_tok += t_tok

        avg_dur = int(sum(i.duration_ms or 0 for i in invs) / max(1, total))
        durations = sorted(i.duration_ms or 0 for i in invs)
        p90_idx = int(len(durations) * 0.9)
        p90_dur = durations[min(p90_idx, len(durations) - 1)] if durations else 0

        # Cost estimation: $0.002 per 1k tokens
        cost = round(total_tok * 0.000002, 4)
        tier = invs[0].tier if invs and invs[0].tier else "T2"

        stat = session.scalar(
            select(ModelStatsDaily).where(
                ModelStatsDaily.project_id == project_id,
                ModelStatsDaily.date == today,
                ModelStatsDaily.model_name == model,
                ModelStatsDaily.task_type == task,
            )
        )
        if not stat:
            stat = ModelStatsDaily(
                project_id=project_id,
                date=today,
                model_name=model,
                tier=tier,
                task_type=task,
            )
            session.add(stat)

        stat.tier = tier
        stat.total_calls = total
        stat.success_calls = success
        stat.failed_calls = failed
        stat.degraded_calls = degraded
        stat.total_prompt_tokens = prompt_tokens
        stat.total_completion_tokens = completion_tokens
        stat.total_tokens = total_tok
        stat.avg_duration_ms = avg_dur
        stat.p90_duration_ms = p90_dur
        stat.estimated_cost = cost
        stats_list.append(stat)

    session.commit()
    return stats_list


def get_model_stats_summary(session: Session, project_id: int) -> dict[str, Any]:
    """Get project wide aggregate token, call, degradation and cost statistics."""
    stats = list(session.scalars(select(ModelStatsDaily).where(ModelStatsDaily.project_id == project_id)).all())
    total_calls = sum(s.total_calls for s in stats)
    success_calls = sum(s.success_calls for s in stats)
    failed_calls = sum(s.failed_calls for s in stats)
    degraded_calls = sum(s.degraded_calls for s in stats)
    total_tokens = sum(s.total_tokens for s in stats)
    estimated_cost = sum(s.estimated_cost for s in stats)

    return {
        "project_id": project_id,
        "total_calls": total_calls,
        "success_calls": success_calls,
        "failed_calls": failed_calls,
        "degraded_calls": degraded_calls,
        "degradation_rate": round(degraded_calls / max(1, total_calls), 3),
        "total_tokens": total_tokens,
        "estimated_cost_usd": round(estimated_cost, 4),
        "records_count": len(stats),
    }


def list_model_stats_daily(session: Session, project_id: int) -> list[ModelStatsDaily]:
    stmt = select(ModelStatsDaily).where(ModelStatsDaily.project_id == project_id).order_by(ModelStatsDaily.date.desc())
    return list(session.scalars(stmt).all())
