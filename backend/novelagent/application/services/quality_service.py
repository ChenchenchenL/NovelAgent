from __future__ import annotations

from typing import Any, Optional
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ...domain.models import Chapter, Scene, SceneRevision
from ...domain.quality_models import BeatContract, QualityReport
from ...domain.quality_rules import detect_semantic_duplicates, detect_vague_and_no_progress
from .beat_service import check_beat_stop_condition, list_scene_beats
from .cliche_service import scan_text_cliches
from .feedback_service import get_active_ignored_rules


def check_scene_quality(
    session: Session,
    project_id: int,
    scene_id: int,
    text_content: str | None = None,
    genre: str | None = None,
) -> QualityReport:
    scene = session.get(Scene, scene_id)
    if not scene:
        raise KeyError(f"场景不存在: ID {scene_id}")

    rev_id: int | None = scene.current_revision_id
    content = text_content
    if content is None:
        if rev_id:
            rev = session.get(SceneRevision, rev_id)
            content = rev.content if rev else ""
        else:
            content = ""

    all_issues: list[dict[str, Any]] = []

    # 1. Semantic repetition & synonym loops
    paragraphs = [p for p in content.split("\n") if p.strip()]
    if len(paragraphs) >= 2:
        all_issues.extend(detect_semantic_duplicates(paragraphs))

    # 2. Cliche and model quirk matching
    all_issues.extend(scan_text_cliches(session, project_id, content, genre=genre))

    # 3. Vague and empty description
    all_issues.extend(detect_vague_and_no_progress(paragraphs))

    # 4. Beat contract check
    beats = list_scene_beats(session, project_id, scene_id)
    word_count = len(content)
    for b in beats:
        if b.status in ("PENDING", "IN_PROGRESS"):
            chk = check_beat_stop_condition(b, word_count)
            if chk.get("should_stop"):
                all_issues.append({
                    "issue_type": "BEAT_STOP_REACHED",
                    "severity": "WARNING",
                    "source_text": f"当前字数: {word_count}",
                    "description": chk["reason"],
                    "evidence": [f"Beat ID {b.id} 停止条件触发"],
                    "suggestion": "当前 Beat 目标已达成，建议停止扩写并开启新叙事节点",
                    "root_cause_id": f"beat_stop_{b.id}",
                })

    # 5. Filter out author ignored issues
    ignored_rules = get_active_ignored_rules(session, project_id, scene_id=scene_id)
    ignored_types = {r.issue_type for r in ignored_rules}
    filtered_issues: list[dict[str, Any]] = []

    # 6. Deduplicate by root_cause_id
    seen_roots: set[str] = set()
    for iss in all_issues:
        itype = iss.get("issue_type", "")
        if itype in ignored_types:
            continue
        rc_id = iss.get("root_cause_id") or itype
        if rc_id not in seen_roots:
            seen_roots.add(rc_id)
            filtered_issues.append(iss)

    # 7. Summary statistics
    blocking_cnt = sum(1 for i in filtered_issues if i.get("severity") == "BLOCKING")
    warning_cnt = sum(1 for i in filtered_issues if i.get("severity") == "WARNING")
    advisory_cnt = sum(1 for i in filtered_issues if i.get("severity") == "ADVISORY")

    summary = {
        "total": len(filtered_issues),
        "blocking": blocking_cnt,
        "warning": warning_cnt,
        "advisory": advisory_cnt,
        "has_blocking": blocking_cnt > 0,
    }

    report = QualityReport(
        project_id=project_id,
        scene_id=scene_id,
        revision_id=rev_id,
        issues=filtered_issues,
        summary=summary,
    )
    session.add(report)
    session.flush()

    # Prune old reports for this scene (keep latest 5)
    existing_reports = list(
        session.scalars(
            select(QualityReport)
            .where(QualityReport.project_id == project_id, QualityReport.scene_id == scene_id)
            .order_by(QualityReport.id.desc())
        ).all()
    )
    if len(existing_reports) > 5:
        for old_r in existing_reports[5:]:
            session.delete(old_r)

    session.commit()
    session.refresh(report)
    return report


def get_latest_quality_report(session: Session, project_id: int, scene_id: int) -> QualityReport | None:
    stmt = (
        select(QualityReport)
        .where(QualityReport.project_id == project_id, QualityReport.scene_id == scene_id)
        .order_by(QualityReport.id.desc())
        .limit(1)
    )
    return session.scalar(stmt)


def list_project_quality_reports(session: Session, project_id: int) -> list[QualityReport]:
    stmt = (
        select(QualityReport)
        .where(QualityReport.project_id == project_id)
        .order_by(QualityReport.id.desc())
    )
    return list(session.scalars(stmt).all())
