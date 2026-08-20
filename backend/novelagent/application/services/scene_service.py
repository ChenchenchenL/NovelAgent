from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ...domain.models import Chapter, CommitJournal, Scene, SceneRevision
from ...domain.rules import validate_scene_status_transition
from ...infrastructure.security import hash_text


def _get_scene_content(session: Session, scene: Scene) -> str:
    if not scene.current_revision_id:
        return ""
    rev = session.get(SceneRevision, scene.current_revision_id)
    return rev.content if rev else ""


def create_scene(
    session: Session,
    project_id: int,
    chapter_id: int,
    title: str | None,
    pov: str | None,
    location: str | None,
) -> Scene:
    chapter = session.get(Chapter, chapter_id)
    if not chapter or chapter.project_id != project_id:
        raise HTTPException(status_code=404, detail="章节不存在")
    max_seq = session.scalar(
        select(func.coalesce(func.max(Scene.sequence), 0)).where(Scene.chapter_id == chapter.id)
    ) or 0
    scene = Scene(
        chapter_id=chapter.id,
        title=title or "未命名场景",
        sequence=max_seq + 1,
        pov=pov,
        location=location,
        status="PLANNED",
    )
    session.add(scene)
    session.commit()
    session.refresh(scene)
    return scene


def get_scene(session: Session, scene_id: int) -> Scene:
    scene = session.get(Scene, scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="场景不存在")
    return scene


def update_scene(session: Session, scene_id: int, title: str | None, pov: str | None, location: str | None) -> Scene:
    scene = get_scene(session, scene_id)
    if title is not None:
        scene.title = title
    if pov is not None:
        scene.pov = pov
    if location is not None:
        scene.location = location
    session.commit()
    return scene


def change_scene_status(session: Session, scene_id: int, new_status: str) -> Scene:
    scene = get_scene(session, scene_id)
    content = _get_scene_content(session, scene)
    try:
        validate_scene_status_transition(scene.status, new_status, has_content=bool(content))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    scene.status = new_status
    session.commit()
    return scene


def create_patch(
    session: Session,
    scene_id: int,
    base_revision_id: int | None,
    content: str,
    source: str = "AUTHOR",
) -> SceneRevision:
    scene = get_scene(session, scene_id)
    if base_revision_id != scene.current_revision_id:
        raise HTTPException(status_code=409, detail="场景基础版本已变化，请重新加载")
    revision = SceneRevision(
        scene_id=scene.id,
        base_revision_id=base_revision_id,
        content=content,
        source=source,
        content_hash=hash_text(content),
    )
    session.add(revision)
    scene.status = "PARTIALLY_ACCEPTED"
    session.commit()
    session.refresh(revision)
    return revision


def accept_revision(session: Session, project_dir: Path, scene_id: int, revision_id: int) -> tuple[Scene, SceneRevision]:
    scene = get_scene(session, scene_id)
    revision = session.get(SceneRevision, revision_id)
    if not revision or revision.scene_id != scene_id:
        raise HTTPException(status_code=404, detail="场景版本不存在")
    if revision.base_revision_id != scene.current_revision_id:
        raise HTTPException(status_code=409, detail="版本冲突")

    scene.current_revision_id = revision.id
    scene.status = "SCENE_ACCEPTED"

    scene_dir = project_dir / ".novelagent" / "text" / "scenes" / f"scene-{scene.id}"
    rev_file = scene_dir / f"rev-{revision.id}.md"
    current_file = scene_dir / "current.md"

    # 2-Phase commit: record journal in PENDING state first
    journal = CommitJournal(
        revision_id=revision.id,
        content_hash=revision.content_hash,
        file_path=str(rev_file),
        file_status="PENDING",
    )
    session.add(journal)
    session.commit()

    # Write files to disk
    scene_dir.mkdir(parents=True, exist_ok=True)
    rev_file.write_text(revision.content, encoding="utf-8")
    current_file.write_text(revision.content, encoding="utf-8")

    # Update journal to COMMITTED state
    journal.file_status = "COMMITTED"
    session.commit()
    return scene, revision


def list_revisions(session: Session, scene_id: int) -> list[SceneRevision]:
    get_scene(session, scene_id)
    return list(session.scalars(
        select(SceneRevision).where(SceneRevision.scene_id == scene_id).order_by(SceneRevision.id.desc())
    ).all())


def get_revision(session: Session, scene_id: int, revision_id: int) -> SceneRevision:
    get_scene(session, scene_id)
    revision = session.get(SceneRevision, revision_id)
    if not revision or revision.scene_id != scene_id:
        raise HTTPException(status_code=404, detail="场景版本不存在")
    return revision


def update_entry_contract(session: Session, scene_id: int, entry_contract: dict[str, Any]) -> Scene:
    scene = get_scene(session, scene_id)
    scene.entry_contract = entry_contract
    session.commit()
    return scene


def update_exit_state(session: Session, scene_id: int, exit_state: dict[str, Any]) -> Scene:
    scene = get_scene(session, scene_id)
    scene.exit_state = exit_state
    session.commit()
    return scene


def delete_scene(session: Session, scene_id: int) -> int:
    scene = get_scene(session, scene_id)
    session.delete(scene)
    session.commit()
    return scene_id
