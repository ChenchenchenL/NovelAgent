from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ...domain.models import Chapter, Project, Scene, Volume
from ...infrastructure.db import make_session_factory

if TYPE_CHECKING:
    from ...api.dependencies import AppState


def open_or_create_project(state: AppState, raw_path: str) -> dict[str, Any]:
    from ...api.dependencies import is_path_allowed

    path = Path(raw_path).expanduser().resolve()
    if not path.is_dir() or not is_path_allowed(path, state.authorized_dirs):
        raise HTTPException(status_code=403, detail="目录未授权")

    db_path = state.settings.db_path(path)
    engine, factory = make_session_factory(db_path)
    state.engine, state.session_factory, state.project_dir = engine, factory, path

    with factory() as db:
        project = db.scalar(select(Project).where(Project.path == str(path)))
        if project is None:
            project = Project(path=str(path), name=path.name or "NovelAgent 项目")
            db.add(project)
            db.flush()
            chapter = Chapter(project_id=project.id, title="第一章", sequence=1, status="IDEA")
            db.add(chapter)
            db.flush()
            scene = Scene(chapter_id=chapter.id, title="第一场", sequence=1)
            db.add(scene)
            db.commit()
        else:
            db.commit()
        return {"id": project.id, "name": project.name, "path": project.path}


def get_current_project(session: Session) -> Project:
    project = session.scalar(select(Project).limit(1))
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


def list_volumes(session: Session, project_id: int) -> list[Volume]:
    return list(session.scalars(
        select(Volume).where(Volume.project_id == project_id).order_by(Volume.sequence)
    ).all())


def create_volume(session: Session, project_id: int, title: str, status: str = "IDEA") -> Volume:
    max_seq = session.scalar(
        select(func.coalesce(func.max(Volume.sequence), 0)).where(Volume.project_id == project_id)
    ) or 0
    volume = Volume(
        project_id=project_id,
        title=title,
        sequence=max_seq + 1,
        status=status or "IDEA",
    )
    session.add(volume)
    session.commit()
    session.refresh(volume)
    return volume


def update_volume(session: Session, project_id: int, volume_id: int, title: str | None, status: str | None) -> Volume:
    volume = session.get(Volume, volume_id)
    if not volume or volume.project_id != project_id:
        raise HTTPException(status_code=404, detail="卷不存在")
    if title is not None:
        volume.title = title
    if status is not None:
        volume.status = status
    session.commit()
    return volume


def delete_volume(session: Session, project_id: int, volume_id: int) -> int:
    volume = session.get(Volume, volume_id)
    if not volume or volume.project_id != project_id:
        raise HTTPException(status_code=404, detail="卷不存在")
    has_chapters = session.scalar(select(Chapter).where(Chapter.volume_id == volume_id).limit(1))
    if has_chapters:
        raise HTTPException(status_code=400, detail="当前卷包含章节，请先移除或删除下属章节")
    session.delete(volume)
    session.commit()
    return volume_id


def build_project_tree(session: Session, project_id: int) -> dict[str, Any]:
    volumes = list_volumes(session, project_id)
    all_chapters = session.scalars(
        select(Chapter).where(Chapter.project_id == project_id).order_by(Chapter.sequence)
    ).all()
    all_scenes = session.scalars(
        select(Scene).join(Chapter, Scene.chapter_id == Chapter.id)
        .where(Chapter.project_id == project_id).order_by(Scene.sequence)
    ).all()

    scenes_by_chapter: dict[int, list[dict[str, Any]]] = {}
    for s in all_scenes:
        scenes_by_chapter.setdefault(s.chapter_id, []).append({
            "id": s.id,
            "chapter_id": s.chapter_id,
            "title": s.title,
            "sequence": s.sequence,
            "pov": s.pov,
            "location": s.location,
            "status": s.status,
            "current_revision_id": s.current_revision_id,
            "entry_contract": s.entry_contract,
            "exit_state": s.exit_state,
        })

    vol_chapters: dict[int, list[dict[str, Any]]] = {}
    unassigned: list[dict[str, Any]] = []
    for c in all_chapters:
        ch_dict = {
            "id": c.id,
            "project_id": c.project_id,
            "volume_id": c.volume_id,
            "title": c.title,
            "sequence": c.sequence,
            "status": c.status,
            "contract": c.contract,
            "scenes": scenes_by_chapter.get(c.id, []),
        }
        if c.volume_id:
            vol_chapters.setdefault(c.volume_id, []).append(ch_dict)
        else:
            unassigned.append(ch_dict)

    vol_list = [
        {
            "id": v.id,
            "project_id": v.project_id,
            "title": v.title,
            "sequence": v.sequence,
            "status": v.status,
            "chapters": vol_chapters.get(v.id, []),
        }
        for v in volumes
    ]
    return {"volumes": vol_list, "unassigned_chapters": unassigned}


def reorder_items(session: Session, project_id: int, item_type: str, parent_id: int | None, order: list[int]) -> None:
    if len(order) != len(set(order)):
        raise HTTPException(status_code=400, detail="排序列表包含重复 ID")

    if item_type == "volume":
        volumes = session.scalars(select(Volume).where(Volume.project_id == project_id, Volume.id.in_(order))).all()
        vol_map = {v.id: v for v in volumes}
        if len(vol_map) != len(order):
            raise HTTPException(status_code=400, detail="排序列表包含无效的卷 ID")
        for idx, vid in enumerate(order):
            vol_map[vid].sequence = idx + 1

    elif item_type == "chapter":
        stmt = select(Chapter).where(Chapter.project_id == project_id, Chapter.id.in_(order))
        if parent_id is not None:
            stmt = stmt.where(Chapter.volume_id == parent_id)
        chapters = session.scalars(stmt).all()
        ch_map = {c.id: c for c in chapters}
        if len(ch_map) != len(order):
            raise HTTPException(status_code=400, detail="排序列表包含无效的章节 ID")
        for idx, cid in enumerate(order):
            ch_map[cid].sequence = idx + 1

    elif item_type == "scene":
        stmt = select(Scene).where(Scene.id.in_(order))
        if parent_id is not None:
            stmt = stmt.where(Scene.chapter_id == parent_id)
        scenes = session.scalars(stmt).all()
        sc_map = {s.id: s for s in scenes}
        if len(sc_map) != len(order):
            raise HTTPException(status_code=400, detail="排序列表包含无效的场景 ID")
        for idx, sid in enumerate(order):
            sc_map[sid].sequence = idx + 1

    session.commit()
