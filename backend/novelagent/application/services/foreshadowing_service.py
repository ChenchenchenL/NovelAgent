from __future__ import annotations

from typing import Any, Optional
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ...domain.models import Chapter, Scene
from ...domain.plot_models import Foreshadowing
from ...domain.transition_rules import check_trigger_condition


def create_foreshadowing(
    session: Session,
    project_id: int,
    name: str,
    setup_scene_id: int,
    plot_thread_id: int | None = None,
    priority: str = "SUBPLOT",
    target_chapter_start: int | None = None,
    target_chapter_end: int | None = None,
    earliest_trigger_chapter: int | None = None,
    latest_payoff_chapter: int | None = None,
    trigger_condition_type: str | None = None,
    trigger_condition_params: dict[str, Any] | None = None,
    visibility: str = "AUTHOR",
    visible_to_character_id: int | None = None,
    anchors: list[dict[str, Any]] | None = None,
    description: str | None = None,
    confirmed: bool = False,
) -> Foreshadowing:
    scene = session.get(Scene, setup_scene_id)
    if not scene:
        raise KeyError(f"埋设场景不存在: ID {setup_scene_id}")
    chapter = session.get(Chapter, scene.chapter_id)
    if not chapter or chapter.project_id != project_id:
        raise KeyError(f"埋设场景不属于当前项目: ID {setup_scene_id}")

    f = Foreshadowing(
        project_id=project_id,
        name=name.strip(),
        setup_scene_id=setup_scene_id,
        plot_thread_id=plot_thread_id,
        status="SETUP",
        priority=priority,
        target_chapter_start=target_chapter_start,
        target_chapter_end=target_chapter_end,
        earliest_trigger_chapter=earliest_trigger_chapter,
        latest_payoff_chapter=latest_payoff_chapter,
        trigger_condition_type=trigger_condition_type,
        trigger_condition_params=trigger_condition_params,
        visibility=visibility,
        visible_to_character_id=visible_to_character_id,
        anchors=anchors or [],
        description=description,
        confirmed=confirmed,
    )
    session.add(f)
    session.commit()
    session.refresh(f)
    return f


def get_foreshadowing(session: Session, foreshadowing_id: int, project_id: int | None = None) -> Foreshadowing:
    f = session.get(Foreshadowing, foreshadowing_id)
    if not f or (project_id is not None and f.project_id != project_id):
        raise KeyError(f"伏笔不存在: ID {foreshadowing_id}")
    return f


def list_foreshadowings(
    session: Session,
    project_id: int,
    status: str | None = None,
    plot_thread_id: int | None = None,
) -> list[Foreshadowing]:
    stmt = select(Foreshadowing).where(Foreshadowing.project_id == project_id)
    if status:
        stmt = stmt.where(Foreshadowing.status == status)
    if plot_thread_id is not None:
        stmt = stmt.where(Foreshadowing.plot_thread_id == plot_thread_id)
    stmt = stmt.order_by(Foreshadowing.id.asc())
    return list(session.scalars(stmt).all())


def update_foreshadowing(
    session: Session,
    foreshadowing_id: int,
    project_id: int | None = None,
    name: str | None = None,
    priority: str | None = None,
    status: str | None = None,
    target_chapter_start: int | None = None,
    target_chapter_end: int | None = None,
    earliest_trigger_chapter: int | None = None,
    latest_payoff_chapter: int | None = None,
    trigger_condition_type: str | None = None,
    trigger_condition_params: dict[str, Any] | None = None,
    visibility: str | None = None,
    visible_to_character_id: int | None = None,
    anchors: list[dict[str, Any]] | None = None,
    description: str | None = None,
) -> Foreshadowing:
    f = get_foreshadowing(session, foreshadowing_id, project_id)
    if name is not None:
        f.name = name.strip()
    if priority is not None:
        f.priority = priority
    if status is not None:
        f.status = status
    if target_chapter_start is not None:
        f.target_chapter_start = target_chapter_start
    if target_chapter_end is not None:
        f.target_chapter_end = target_chapter_end
    if earliest_trigger_chapter is not None:
        f.earliest_trigger_chapter = earliest_trigger_chapter
    if latest_payoff_chapter is not None:
        f.latest_payoff_chapter = latest_payoff_chapter
    if trigger_condition_type is not None:
        f.trigger_condition_type = trigger_condition_type
    if trigger_condition_params is not None:
        f.trigger_condition_params = trigger_condition_params
    if visibility is not None:
        f.visibility = visibility
    if visible_to_character_id is not None:
        f.visible_to_character_id = visible_to_character_id
    if anchors is not None:
        f.anchors = anchors
    if description is not None:
        f.description = description

    session.commit()
    session.refresh(f)
    return f


def payoff_foreshadowing(
    session: Session,
    foreshadowing_id: int,
    payoff_scene_id: int,
    project_id: int | None = None,
    description: str | None = None,
) -> Foreshadowing:
    f = get_foreshadowing(session, foreshadowing_id, project_id)
    scene = session.get(Scene, payoff_scene_id)
    if not scene:
        raise KeyError(f"回收场景不存在: ID {payoff_scene_id}")
    if project_id is not None:
        chapter = session.get(Chapter, scene.chapter_id)
        if not chapter or chapter.project_id != project_id:
            raise KeyError(f"回收场景不属于当前项目: ID {payoff_scene_id}")

    f.status = "PAYOFF"
    f.payoff_scene_id = payoff_scene_id
    if description:
        f.description = description
    session.commit()
    session.refresh(f)
    return f


def delete_foreshadowing(session: Session, foreshadowing_id: int, project_id: int | None = None) -> None:
    f = get_foreshadowing(session, foreshadowing_id, project_id)
    session.delete(f)
    session.commit()


def schedule_foreshadowings_for_scene(
    session: Session,
    project_id: int,
    scene_id: int,
    context: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    scene = session.get(Scene, scene_id)
    if not scene:
        raise KeyError(f"场景不存在: ID {scene_id}")
    chapter = session.get(Chapter, scene.chapter_id)
    if not chapter or chapter.project_id != project_id:
        raise KeyError(f"场景不属于当前项目: ID {scene_id}")
    current_chap_seq = chapter.sequence if chapter else 1

    ctx = context or {}
    candidates = list(
        session.scalars(
            select(Foreshadowing).where(
                Foreshadowing.project_id == project_id,
                Foreshadowing.status.in_(["SETUP", "DEVELOP"]),
                or_(
                    Foreshadowing.target_chapter_start <= current_chap_seq,
                    Foreshadowing.target_chapter_start.is_(None),
                ),
            )
        ).all()
    )

    scheduled = []
    for f in candidates:
        matched = check_trigger_condition(f.trigger_condition_type, f.trigger_condition_params, ctx)
        in_window = f.target_chapter_start is None or (
            f.target_chapter_start <= current_chap_seq
            and (f.target_chapter_end is None or current_chap_seq <= f.target_chapter_end)
        )
        is_overdue = f.latest_payoff_chapter is not None and current_chap_seq > f.latest_payoff_chapter

        if matched or in_window or is_overdue:
            scheduled.append({
                "foreshadowing_id": f.id,
                "name": f.name,
                "status": f.status,
                "priority": f.priority,
                "is_triggered": matched,
                "is_in_window": in_window,
                "is_overdue": is_overdue,
                "trigger_condition_type": f.trigger_condition_type,
                "anchors": f.anchors or [],
            })

    priority_map = {"MAIN": 0, "SUBPLOT": 1, "BACKGROUND": 2}
    scheduled.sort(key=lambda x: (0 if x["is_triggered"] else 1, priority_map.get(x["priority"], 3), x["foreshadowing_id"]))
    return scheduled
