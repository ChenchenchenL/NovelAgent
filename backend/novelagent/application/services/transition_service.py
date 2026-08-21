from __future__ import annotations

from typing import Any, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...domain.models import Chapter, Scene
from ...domain.transition_rules import evaluate_scene_transition


def check_scene_transition_service(
    session: Session,
    scene_id: int,
    project_id: int | None = None,
    prev_scene_id: int | None = None,
    entry_contract_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    scene = session.get(Scene, scene_id)
    if not scene:
        raise KeyError(f"场景不存在: ID {scene_id}")
    if project_id is not None:
        chapter = session.get(Chapter, scene.chapter_id)
        if not chapter or chapter.project_id != project_id:
            raise KeyError(f"场景不属于当前项目: ID {scene_id}")

    if prev_scene_id is None:
        stmt = (
            select(Scene)
            .where(Scene.chapter_id == scene.chapter_id, Scene.sequence < scene.sequence)
            .order_by(Scene.sequence.desc())
        )
        prev_scene = session.scalar(stmt)
    else:
        prev_scene = session.get(Scene, prev_scene_id)
        if not prev_scene:
            raise KeyError(f"前置场景不存在: ID {prev_scene_id}")
        if project_id is not None:
            prev_chap = session.get(Chapter, prev_scene.chapter_id)
            if not prev_chap or prev_chap.project_id != project_id:
                raise KeyError(f"前置场景不属于当前项目: ID {prev_scene_id}")

    prev_exit = prev_scene.exit_state if prev_scene else {}
    curr_entry = entry_contract_override or scene.entry_contract or {}

    res = evaluate_scene_transition(prev_exit, curr_entry)
    res["scene_id"] = scene_id
    res["prev_scene_id"] = prev_scene.id if prev_scene else None
    return res


def update_scene_contracts(
    session: Session,
    scene_id: int,
    project_id: int | None = None,
    entry_contract: dict[str, Any] | None = None,
    exit_state: dict[str, Any] | None = None,
) -> Scene:
    scene = session.get(Scene, scene_id)
    if not scene:
        raise KeyError(f"场景不存在: ID {scene_id}")
    if project_id is not None:
        chapter = session.get(Chapter, scene.chapter_id)
        if not chapter or chapter.project_id != project_id:
            raise KeyError(f"场景不属于当前项目: ID {scene_id}")

    if entry_contract is not None:
        merged_entry = dict(scene.entry_contract or {})
        merged_entry.update(entry_contract)
        scene.entry_contract = merged_entry

    if exit_state is not None:
        merged_exit = dict(scene.exit_state or {})
        merged_exit.update(exit_state)
        scene.exit_state = merged_exit

    session.commit()
    session.refresh(scene)
    return scene
