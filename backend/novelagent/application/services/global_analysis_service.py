from __future__ import annotations

import time
from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...domain.continuity_models import Character, CharacterState, LocationEntity, MovementEvent, RelationshipEvent
from ...domain.graphrag_models import GlobalAnalysisReport
from ...domain.graphrag_rules import (
    analyze_character_arc,
    analyze_foreshadow_fulfillment,
    analyze_plot_ruptures,
)
from ...domain.models import Chapter, Scene
from ...domain.plot_models import Foreshadowing, PlotEvent, PlotThread
from ...domain.quality_models import VoiceFingerprint
from ...domain.rules import estimate_tokens


def run_character_arcs_analysis(session: Session, project_id: int) -> GlobalAnalysisReport:
    """Analyze growth arcs and turning points for all characters in the project."""
    start_t = time.perf_counter()
    chars = session.scalars(select(Character).where(Character.project_id == project_id)).all()
    arcs = []

    for c in chars:
        states = list(
            session.scalars(
                select(CharacterState).where(CharacterState.character_id == c.id).order_by(CharacterState.scene_id.asc())
            ).all()
        )
        st_dicts = [{"scene_id": s.scene_id, "location": s.location, "emotion": s.emotion, "arc_stage": s.arc_stage, "narrative_time": s.narrative_time} for s in states]
        arc = analyze_character_arc(c.name, st_dicts)
        arcs.append(arc)

    content = {"character_arcs": arcs, "analyzed_characters_count": len(chars)}
    summary = f"全书人物弧回顾完成，共分析 {len(chars)} 名角色成长轨迹与阶段转变。"
    dur = int((time.perf_counter() - start_t) * 1000)

    rep = GlobalAnalysisReport(
        project_id=project_id,
        report_type="CHARACTER_ARC",
        content=content,
        summary=summary,
        affected_entities=[c.id for c in chars],
        severity_counts={"total_arcs": len(arcs)},
        token_cost=estimate_tokens(summary),
        duration_ms=dur,
    )
    session.add(rep)
    session.commit()
    session.refresh(rep)
    return rep


def run_relationship_network_analysis(session: Session, project_id: int) -> GlobalAnalysisReport:
    """Analyze global relationship graph and event density."""
    start_t = time.perf_counter()
    events = list(session.scalars(select(RelationshipEvent).where(RelationshipEvent.project_id == project_id)).all())
    rel_map: dict[str, int] = {}
    for ev in events:
        key = f"{ev.subject_character_id}->{ev.object_character_id}:{ev.relationship_type}"
        rel_map[key] = rel_map.get(key, 0) + 1

    content = {"relationships": rel_map, "total_events": len(events)}
    summary = f"全书人物关系网络分析完成，记录跨角色关系事件 {len(events)} 次，独特关系链 {len(rel_map)} 条。"
    dur = int((time.perf_counter() - start_t) * 1000)

    rep = GlobalAnalysisReport(
        project_id=project_id,
        report_type="RELATIONSHIP_NETWORK",
        content=content,
        summary=summary,
        token_cost=estimate_tokens(summary),
        duration_ms=dur,
    )
    session.add(rep)
    session.commit()
    session.refresh(rep)
    return rep


def run_foreshadow_audit(session: Session, project_id: int) -> GlobalAnalysisReport:
    """Audit project foreshadowing setup and resolution rates."""
    start_t = time.perf_counter()
    foreshadowings = list(session.scalars(select(Foreshadowing).where(Foreshadowing.project_id == project_id)).all())
    scene_cnt = session.scalar(select(Scene).join(Chapter).where(Chapter.project_id == project_id))

    f_dicts = [{"id": f.id, "name": f.name, "status": f.status, "target_chapter_end": f.target_chapter_end} for f in foreshadowings]
    audit = analyze_foreshadow_fulfillment(f_dicts)
    summary = f"全书伏笔审计完成：共设置伏笔 {audit['total']} 条，已兑现 {audit['fulfilled']} 条，兑现率 {int(audit['fulfillment_rate'] * 100)}%。"
    dur = int((time.perf_counter() - start_t) * 1000)

    rep = GlobalAnalysisReport(
        project_id=project_id,
        report_type="FORESHADOW_AUDIT",
        content=audit,
        summary=summary,
        affected_entities=[f.id for f in foreshadowings],
        severity_counts={"overdue": len(audit["overdue_items"])},
        token_cost=estimate_tokens(summary),
        duration_ms=dur,
    )
    session.add(rep)
    session.commit()
    session.refresh(rep)
    return rep


def run_plot_rupture_audit(session: Session, project_id: int) -> GlobalAnalysisReport:
    """Detect broken, forgotten or dormant plot threads."""
    start_t = time.perf_counter()
    threads = list(session.scalars(select(PlotThread).where(PlotThread.project_id == project_id)).all())
    events = list(session.scalars(select(PlotEvent).join(PlotThread).where(PlotThread.project_id == project_id)).all())
    scenes = list(session.scalars(select(Scene).join(Chapter).where(Chapter.project_id == project_id)).all())

    t_dicts = [{"id": t.id, "name": t.name, "status": t.status} for t in threads]
    ev_dicts = [{"thread_id": e.thread_id, "scene_id": e.scene_id} for e in events]

    ruptures = analyze_plot_ruptures(t_dicts, ev_dicts, len(scenes))
    summary = f"全书剧情断裂审计完成：共检测到 {len(ruptures)} 处潜在休眠或未决剧情线索风险。"
    dur = int((time.perf_counter() - start_t) * 1000)

    rep = GlobalAnalysisReport(
        project_id=project_id,
        report_type="PLOT_RUPTURE",
        content={"ruptures": ruptures, "total_threads": len(threads)},
        summary=summary,
        severity_counts={"warnings": len(ruptures)},
        token_cost=estimate_tokens(summary),
        duration_ms=dur,
    )
    session.add(rep)
    session.commit()
    session.refresh(rep)
    return rep


def list_global_analysis_reports(session: Session, project_id: int, report_type: str | None = None) -> list[GlobalAnalysisReport]:
    stmt = select(GlobalAnalysisReport).where(GlobalAnalysisReport.project_id == project_id)
    if report_type:
        stmt = stmt.where(GlobalAnalysisReport.report_type == report_type)
    return list(session.scalars(stmt.order_by(GlobalAnalysisReport.id.desc())).all())


def get_global_analysis_report(session: Session, report_id: int, project_id: int) -> GlobalAnalysisReport:
    rep = session.scalar(
        select(GlobalAnalysisReport).where(GlobalAnalysisReport.id == report_id, GlobalAnalysisReport.project_id == project_id)
    )
    if not rep:
        raise KeyError(f"全局分析报告不存在: ID {report_id}")
    return rep
