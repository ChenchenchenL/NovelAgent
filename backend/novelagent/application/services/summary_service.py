from __future__ import annotations

import json
from typing import Any, Optional
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from ...domain.continuity_models import Character
from ...domain.models import Chapter, Project, Scene, SceneRevision, Volume
from ...domain.plot_models import PlotThread
from ...domain.search_models import SummaryArtifact
from ...domain.transition_rules import estimate_tokens


def create_or_update_summary(
    session: Session,
    project_id: int,
    summary_type: str,
    source_id: int,
    source_version: int,
    content: str,
    covered_node_ids: list[int] | None = None,
    narrative_time_range: str | None = None,
) -> SummaryArtifact:
    summ = session.scalar(
        select(SummaryArtifact).where(
            SummaryArtifact.project_id == project_id,
            SummaryArtifact.summary_type == summary_type,
            SummaryArtifact.source_id == source_id,
        )
    )
    if not summ:
        summ = SummaryArtifact(
            project_id=project_id,
            summary_type=summary_type,
            source_id=source_id,
            source_version=source_version,
            content=content.strip(),
            covered_node_ids=covered_node_ids or [],
            narrative_time_range=narrative_time_range,
        )
        session.add(summ)
    else:
        summ.source_version = source_version
        summ.content = content.strip()
        summ.covered_node_ids = covered_node_ids or []
        summ.narrative_time_range = narrative_time_range
    session.commit()
    session.refresh(summ)
    return summ


def get_summary(session: Session, project_id: int, summary_type: str, source_id: int) -> SummaryArtifact | None:
    return session.scalar(
        select(SummaryArtifact).where(
            SummaryArtifact.project_id == project_id,
            SummaryArtifact.summary_type == summary_type,
            SummaryArtifact.source_id == source_id,
        )
    )


def list_summaries(session: Session, project_id: int, summary_type: str | None = None) -> list[SummaryArtifact]:
    stmt = select(SummaryArtifact).where(SummaryArtifact.project_id == project_id)
    if summary_type:
        stmt = stmt.where(SummaryArtifact.summary_type == summary_type)
    return list(session.scalars(stmt.order_by(SummaryArtifact.id.asc())).all())


def hierarchical_retrieve(
    session: Session,
    project_id: int,
    scene_id: int,
    max_tokens: int = 4000,
    include_plot_threads: bool = True,
    include_adjacent_scenes: bool = True,
    include_recent_text: bool = True,
) -> list[dict[str, Any]]:
    scene = session.get(Scene, scene_id)
    if not scene:
        raise KeyError(f"场景不存在: ID {scene_id}")
    chapter = session.get(Chapter, scene.chapter_id)
    if not chapter or chapter.project_id != project_id:
        raise KeyError(f"场景不属于当前项目: ID {scene_id}")

    fragments: list[dict[str, Any]] = []
    used_tokens = 0

    # 1. Project / Volume summary
    proj_sum = get_summary(session, project_id, "PROJECT", project_id)
    if proj_sum and proj_sum.content:
        cost = estimate_tokens(proj_sum.content)
        fragments.append({
            "type": "PROJECT_SUMMARY",
            "content": proj_sum.content,
            "source_id": project_id,
            "version": proj_sum.source_version,
            "tokens": cost,
        })
        used_tokens += cost

    # 2. Active Plot Threads summaries
    if include_plot_threads:
        threads = session.scalars(
            select(PlotThread).where(PlotThread.project_id == project_id, PlotThread.status == "ACTIVE")
        ).all()
        for t in threads:
            t_sum = get_summary(session, project_id, "PLOT_THREAD", t.id)
            desc = t_sum.content if t_sum else (t.description or f"剧情线: {t.name}")
            cost = estimate_tokens(desc)
            if used_tokens + cost <= max_tokens:
                fragments.append({
                    "type": "PLOT_THREAD_SUMMARY",
                    "content": desc,
                    "source_id": t.id,
                    "version": t_sum.source_version if t_sum else 1,
                    "tokens": cost,
                })
                used_tokens += cost

    # 3. Adjacent Scene Exit State & Entry Contract
    if include_adjacent_scenes:
        prev_scene = session.scalar(
            select(Scene)
            .where(Scene.chapter_id == scene.chapter_id, Scene.sequence < scene.sequence)
            .order_by(Scene.sequence.desc())
        )
        if prev_scene and prev_scene.exit_state:
            txt = json.dumps(prev_scene.exit_state, ensure_ascii=False)
            cost = estimate_tokens(txt)
            if used_tokens + cost <= max_tokens:
                fragments.append({
                    "type": "SCENE_EXIT_STATE",
                    "content": txt,
                    "source_id": prev_scene.id,
                    "version": prev_scene.current_revision_id or 1,
                    "tokens": cost,
                })
                used_tokens += cost

    # 4. Recent scene text
    if include_recent_text and scene.current_revision_id:
        rev = session.get(SceneRevision, scene.current_revision_id)
        if rev and rev.content:
            recent = rev.content[-800:] if len(rev.content) > 800 else rev.content
            cost = estimate_tokens(recent)
            if used_tokens + cost <= max_tokens:
                fragments.append({
                    "type": "RECENT_TEXT",
                    "content": recent,
                    "source_id": scene.id,
                    "version": rev.id,
                    "tokens": cost,
                })
                used_tokens += cost

    return fragments


def rebuild_summaries(session: Session, project_id: int) -> int:
    session.execute(delete(SummaryArtifact).where(SummaryArtifact.project_id == project_id))
    session.commit()

    count = 0
    # Project summary
    proj = session.get(Project, project_id)
    if proj:
        create_or_update_summary(session, project_id, "PROJECT", proj.id, 1, f"作品《{proj.name}》的正典总览。")
        count += 1

    # PlotThread summaries
    threads = session.scalars(select(PlotThread).where(PlotThread.project_id == project_id)).all()
    for t in threads:
        create_or_update_summary(session, project_id, "PLOT_THREAD", t.id, 1, f"【{t.thread_type}】{t.name}: {t.description or '进行中'}")
        count += 1

    # Character summaries
    chars = session.scalars(select(Character).where(Character.project_id == project_id)).all()
    for c in chars:
        create_or_update_summary(session, project_id, "CHARACTER", c.id, 1, f"角色 {c.name}: {c.description or '登场人物'}")
        count += 1

    return count
