from __future__ import annotations

from typing import Any, Optional
from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from ...domain.models import Chapter, Scene
from ...domain.plot_models import Foreshadowing, PlotEvent, PlotThread

VALID_THREAD_STATUSES = {"ACTIVE", "RESOLVED", "ABANDONED", "SUSPENDED"}
VALID_EVENT_TYPES = {"INTRODUCTION", "DEVELOPMENT", "TWIST", "DELAY", "RESOLUTION", "ABANDONED"}


def create_plot_thread(
    session: Session,
    project_id: int,
    name: str,
    thread_type: str = "MAIN",
    priority: int = 1,
    description: str | None = None,
    start_scene_id: int | None = None,
) -> PlotThread:
    thread = PlotThread(
        project_id=project_id,
        name=name.strip(),
        thread_type=thread_type,
        status="ACTIVE",
        priority=priority,
        description=description,
        start_scene_id=start_scene_id,
    )
    session.add(thread)
    session.commit()
    session.refresh(thread)
    return thread


def get_plot_thread(session: Session, thread_id: int, project_id: int | None = None) -> PlotThread:
    thread = session.get(PlotThread, thread_id)
    if not thread or (project_id is not None and thread.project_id != project_id):
        raise KeyError(f"剧情线不存在: ID {thread_id}")
    return thread


def list_plot_threads(session: Session, project_id: int) -> list[PlotThread]:
    stmt = select(PlotThread).where(PlotThread.project_id == project_id).order_by(PlotThread.priority.asc(), PlotThread.id.asc())
    return list(session.scalars(stmt).all())


def update_plot_thread(
    session: Session,
    thread_id: int,
    project_id: int | None = None,
    name: str | None = None,
    thread_type: str | None = None,
    status: str | None = None,
    priority: int | None = None,
    description: str | None = None,
    start_scene_id: int | None = None,
    end_scene_id: int | None = None,
) -> PlotThread:
    thread = get_plot_thread(session, thread_id, project_id)
    if name is not None:
        thread.name = name.strip()
    if thread_type is not None:
        thread.thread_type = thread_type
    if status is not None:
        if status not in VALID_THREAD_STATUSES:
            raise ValueError(f"非法剧情线状态: {status}")
        thread.status = status
    if priority is not None:
        thread.priority = priority
    if description is not None:
        thread.description = description
    if start_scene_id is not None:
        thread.start_scene_id = start_scene_id
    if end_scene_id is not None:
        thread.end_scene_id = end_scene_id
    session.commit()
    session.refresh(thread)
    return thread


def delete_plot_thread(session: Session, thread_id: int, project_id: int | None = None) -> None:
    thread = get_plot_thread(session, thread_id, project_id)
    # Cascade cleanup plot events and unlink foreshadowings
    session.execute(delete(PlotEvent).where(PlotEvent.plot_thread_id == thread_id))
    session.execute(
        update(Foreshadowing).where(Foreshadowing.plot_thread_id == thread_id).values(plot_thread_id=None)
    )
    session.delete(thread)
    session.commit()


def create_plot_event(
    session: Session,
    plot_thread_id: int,
    event_type: str,
    scene_id: int,
    description: str,
    project_id: int | None = None,
    narrative_time: str | None = None,
    evidence: str | None = None,
    confirmed: bool = False,
) -> PlotEvent:
    thread = get_plot_thread(session, plot_thread_id, project_id)
    scene = session.get(Scene, scene_id)
    if not scene:
        raise KeyError(f"场景不存在: ID {scene_id}")
    if project_id is not None:
        chapter = session.get(Chapter, scene.chapter_id)
        if not chapter or chapter.project_id != project_id:
            raise KeyError(f"场景不属于当前项目: ID {scene_id}")

    if event_type not in VALID_EVENT_TYPES:
        raise ValueError(f"非法剧情事件类型: {event_type}")

    evt = PlotEvent(
        plot_thread_id=plot_thread_id,
        event_type=event_type,
        scene_id=scene_id,
        narrative_time=narrative_time,
        description=description.strip(),
        evidence=evidence,
        confirmed=confirmed,
    )
    session.add(evt)

    if event_type == "RESOLUTION":
        thread.status = "RESOLVED"
        thread.end_scene_id = scene_id
    elif event_type == "ABANDONED":
        thread.status = "ABANDONED"
        thread.end_scene_id = scene_id

    session.commit()
    session.refresh(evt)
    return evt


def list_plot_events(session: Session, plot_thread_id: int | None = None, scene_id: int | None = None) -> list[PlotEvent]:
    stmt = select(PlotEvent)
    if plot_thread_id is not None:
        stmt = stmt.where(PlotEvent.plot_thread_id == plot_thread_id)
    if scene_id is not None:
        stmt = stmt.where(PlotEvent.scene_id == scene_id)
    stmt = stmt.order_by(PlotEvent.id.asc())
    return list(session.scalars(stmt).all())
