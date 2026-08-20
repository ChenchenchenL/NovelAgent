from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ...domain.models import Chapter, Scene, Volume
from ...domain.rules import validate_chapter_status_transition


def list_chapters(session: Session, project_id: int) -> list[Chapter]:
    return list(session.scalars(
        select(Chapter).where(Chapter.project_id == project_id).order_by(Chapter.sequence)
    ).all())


def get_chapter(session: Session, project_id: int, chapter_id: int) -> tuple[Chapter, list[Scene]]:
    chapter = session.get(Chapter, chapter_id)
    if not chapter or chapter.project_id != project_id:
        raise HTTPException(status_code=404, detail="章节不存在")
    scenes = list(session.scalars(
        select(Scene).where(Scene.chapter_id == chapter.id).order_by(Scene.sequence)
    ).all())
    return chapter, scenes


def create_chapter(
    session: Session,
    project_id: int,
    title: str,
    volume_id: int | None = None,
    status: str = "IDEA",
    contract: dict[str, Any] | None = None,
) -> Chapter:
    if volume_id is not None:
        vol = session.get(Volume, volume_id)
        if not vol or vol.project_id != project_id:
            raise HTTPException(status_code=400, detail="指定的卷不存在或不属于当前项目")
    max_seq = session.scalar(
        select(func.coalesce(func.max(Chapter.sequence), 0)).where(Chapter.project_id == project_id)
    ) or 0
    chapter = Chapter(
        project_id=project_id,
        volume_id=volume_id,
        title=title,
        sequence=max_seq + 1,
        status=status or "IDEA",
        contract=contract,
    )
    session.add(chapter)
    session.commit()
    session.refresh(chapter)
    return chapter


def update_chapter(
    session: Session,
    project_id: int,
    chapter_id: int,
    title: str | None,
    volume_id: int | None,
    contract: dict[str, Any] | None,
) -> Chapter:
    chapter = session.get(Chapter, chapter_id)
    if not chapter or chapter.project_id != project_id:
        raise HTTPException(status_code=404, detail="章节不存在")
    if volume_id is not None:
        if volume_id != 0:
            vol = session.get(Volume, volume_id)
            if not vol or vol.project_id != project_id:
                raise HTTPException(status_code=400, detail="指定的卷不存在或不属于当前项目")
            chapter.volume_id = volume_id
        else:
            chapter.volume_id = None
    if title is not None:
        chapter.title = title
    if contract is not None:
        chapter.contract = contract
    session.commit()
    return chapter


def change_chapter_status(session: Session, project_id: int, chapter_id: int, new_status: str) -> Chapter:
    chapter = session.get(Chapter, chapter_id)
    if not chapter or chapter.project_id != project_id:
        raise HTTPException(status_code=404, detail="章节不存在")
    scenes = session.scalars(select(Scene).where(Scene.chapter_id == chapter.id)).all()
    scene_statuses = [s.status for s in scenes]
    try:
        validate_chapter_status_transition(chapter.status, new_status, scene_statuses)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    chapter.status = new_status
    session.commit()
    return chapter


def delete_chapter(session: Session, project_id: int, chapter_id: int) -> int:
    chapter = session.get(Chapter, chapter_id)
    if not chapter or chapter.project_id != project_id:
        raise HTTPException(status_code=404, detail="章节不存在")
    if chapter.status == "RELEASED":
        raise HTTPException(status_code=400, detail="已发布章节不可删除")
    has_scenes = session.scalar(select(Scene).where(Scene.chapter_id == chapter.id).limit(1))
    if has_scenes:
        raise HTTPException(status_code=400, detail="当前章节包含场景，请先删除下属场景")
    session.delete(chapter)
    session.commit()
    return chapter_id
