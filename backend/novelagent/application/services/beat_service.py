from __future__ import annotations

from typing import Any, Optional
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ...domain.models import Scene
from ...domain.quality_models import BeatContract


def _are_all_advancements_achieved(
    required: list[dict[str, Any]],
    achieved: list[dict[str, Any]],
) -> bool:
    if not required:
        return True
    if len(achieved) < len(required):
        return False

    req_counts: dict[str, int] = {}
    for r in required:
        t = r.get("type", "NEW_ACTION")
        req_counts[t] = req_counts.get(t, 0) + 1

    ach_counts: dict[str, int] = {}
    for a in achieved:
        t = a.get("type", "NEW_ACTION")
        ach_counts[t] = ach_counts.get(t, 0) + 1

    for t, needed in req_counts.items():
        if ach_counts.get(t, 0) < needed:
            return False
    return True


def create_beat_contract(
    session: Session,
    project_id: int,
    scene_id: int,
    required_advancements: list[dict[str, Any]] | None = None,
    stop_conditions: list[dict[str, Any]] | None = None,
    target_word_count: int | None = None,
    max_word_count: int | None = None,
    forbidden_patterns: list[str] | None = None,
    generation_run_id: int | None = None,
) -> BeatContract:
    if not session.get(Scene, scene_id):
        raise KeyError(f"场景不存在: ID {scene_id}")

    beat = BeatContract(
        project_id=project_id,
        scene_id=scene_id,
        generation_run_id=generation_run_id,
        required_advancements=required_advancements or [],
        stop_conditions=stop_conditions or [],
        target_word_count=target_word_count,
        max_word_count=max_word_count,
        forbidden_patterns=forbidden_patterns or [],
        status="PENDING",
        advancements_achieved=[],
        actual_word_count=0,
    )
    session.add(beat)
    session.commit()
    session.refresh(beat)
    return beat


def get_beat_contract(session: Session, beat_id: int, project_id: int) -> BeatContract:
    beat = session.scalar(
        select(BeatContract).where(BeatContract.id == beat_id, BeatContract.project_id == project_id)
    )
    if not beat:
        raise KeyError(f"Beat 契约不存在: ID {beat_id}")
    return beat


def list_scene_beats(session: Session, project_id: int, scene_id: int) -> list[BeatContract]:
    stmt = (
        select(BeatContract)
        .where(BeatContract.project_id == project_id, BeatContract.scene_id == scene_id)
        .order_by(BeatContract.id.asc())
    )
    return list(session.scalars(stmt).all())


def update_beat_contract(
    session: Session,
    beat_id: int,
    project_id: int,
    required_advancements: list[dict[str, Any]] | None = None,
    stop_conditions: list[dict[str, Any]] | None = None,
    target_word_count: int | None = None,
    max_word_count: int | None = None,
    forbidden_patterns: list[str] | None = None,
) -> BeatContract:
    beat = get_beat_contract(session, beat_id, project_id)
    if required_advancements is not None:
        beat.required_advancements = required_advancements
    if stop_conditions is not None:
        beat.stop_conditions = stop_conditions
    if target_word_count is not None:
        beat.target_word_count = target_word_count
    if max_word_count is not None:
        beat.max_word_count = max_word_count
    if forbidden_patterns is not None:
        beat.forbidden_patterns = forbidden_patterns

    session.commit()
    session.refresh(beat)
    return beat


def advance_beat(
    session: Session,
    beat_id: int,
    project_id: int,
    advancement: dict[str, Any],
) -> BeatContract:
    beat = get_beat_contract(session, beat_id, project_id)
    achieved = list(beat.advancements_achieved or [])
    achieved.append(advancement)
    beat.advancements_achieved = achieved

    if _are_all_advancements_achieved(beat.required_advancements or [], achieved):
        beat.status = "COMPLETED"
    else:
        beat.status = "IN_PROGRESS"

    session.commit()
    session.refresh(beat)
    return beat


def stop_beat(
    session: Session,
    beat_id: int,
    project_id: int,
    reason: str = "MANUAL_STOP",
    actual_word_count: int | None = None,
) -> BeatContract:
    beat = get_beat_contract(session, beat_id, project_id)
    beat.status = "STOPPED"
    if actual_word_count is not None:
        beat.actual_word_count = actual_word_count
        if beat.max_word_count and actual_word_count > beat.max_word_count:
            beat.status = "OVERRUN"

    session.commit()
    session.refresh(beat)
    return beat


def check_beat_stop_condition(beat: BeatContract, current_word_count: int) -> dict[str, Any]:
    """Check if generation meets any stop conditions."""
    if beat.max_word_count and current_word_count >= beat.max_word_count:
        return {"should_stop": True, "reason": f"达到最大字数上限 ({beat.max_word_count} 字)"}

    if beat.target_word_count:
        tolerance = 0.2
        target = beat.target_word_count
        if current_word_count >= int(target * (1.0 + tolerance)):
            return {"should_stop": True, "reason": f"超出目标字数软范围 (+20%: {current_word_count} 字)"}

    for cond in (beat.stop_conditions or []):
        c_type = cond.get("type")
        if c_type == "WORD_COUNT":
            t = cond.get("target", beat.target_word_count or 1000)
            tol = cond.get("tolerance", 0.2)
            if current_word_count >= int(t * (1.0 + tol)):
                return {"should_stop": True, "reason": f"满足停止条件: 字数达到 {current_word_count} (目标 {t})"}
        elif c_type == "ALL_ADVANCEMENTS_DONE":
            if _are_all_advancements_achieved(beat.required_advancements or [], beat.advancements_achieved or []):
                return {"should_stop": True, "reason": "满足停止条件: 所有声明的推进已完成"}

    return {"should_stop": False, "reason": ""}
