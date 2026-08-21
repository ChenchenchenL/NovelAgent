from __future__ import annotations

import logging
from typing import Any

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ...domain.models import CanonClaim, Chapter, ClaimCandidate, EntityAlias, GenerationWorkspace, Scene, SceneRevision
from ...integrations.extraction import extract_candidates

logger = logging.getLogger(__name__)


def _get_scene_text(session: Session, scene: Scene, revision_id: int | None = None) -> tuple[str, int | None]:
    if revision_id:
        rev = session.get(SceneRevision, revision_id)
        if rev:
            return rev.content, rev.id
    if scene.current_revision_id:
        rev = session.get(SceneRevision, scene.current_revision_id)
        if rev:
            return rev.content, rev.id
    latest_rev = session.scalar(
        select(SceneRevision).where(SceneRevision.scene_id == scene.id).order_by(SceneRevision.id.desc()).limit(1)
    )
    if latest_rev and latest_rev.content:
        return latest_rev.content, latest_rev.id
    ws = session.scalar(select(GenerationWorkspace).where(GenerationWorkspace.scene_id == scene.id))
    if ws and ws.draft_content:
        return ws.draft_content, None
    return "", None


def extract_scene_claims(
    session: Session,
    scene_id: int,
    revision_id: int | None = None,
    force_full_scan: bool = False,
) -> dict[str, Any]:
    scene = session.get(Scene, scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="场景不存在")

    text, rev_id = _get_scene_text(session, scene, revision_id)
    if not text.strip():
        return {
            "scene_id": scene_id,
            "candidate_count": 0,
            "auto_confirmed_count": 0,
            "pending_review_count": 0,
            "candidates": [],
        }

    chapter = session.get(Chapter, scene.chapter_id)
    project_id = chapter.project_id if chapter else 1
    aliases = list(session.scalars(select(EntityAlias).where(EntityAlias.project_id == project_id)).all())
    alias_map = {a.alias_name: a.canonical_name for a in aliases}

    if force_full_scan:
        session.execute(
            delete(ClaimCandidate).where(
                ClaimCandidate.scene_id == scene_id,
                ClaimCandidate.status.in_(["REVIEW_REQUIRED", "AUTO_CONFIRMED"]),
            )
        )

    raw_candidates = extract_candidates(text, known_aliases=alias_map)
    created_candidates: list[ClaimCandidate] = []
    auto_confirmed_count = 0

    for raw in raw_candidates:
        cand = ClaimCandidate(
            scene_id=scene_id,
            subject=raw.subject,
            predicate=raw.predicate,
            object_value=raw.object_value,
            modality=raw.modality,
            cognitive_subject=raw.cognitive_subject,
            source_start=raw.source_start,
            source_end=raw.source_end,
            paragraph_index=raw.paragraph_index,
            source_text=raw.source_text,
            content_hash=raw.content_hash,
            confidence=raw.confidence,
            entity_confidence=raw.entity_confidence,
            hypothesis_tags=raw.hypothesis_tags,
            status=raw.status,
        )
        session.add(cand)
        session.flush()
        created_candidates.append(cand)

        if raw.status == "AUTO_CONFIRMED":
            canon = CanonClaim(
                project_id=project_id,
                subject=raw.subject,
                predicate=raw.predicate,
                object_value=raw.object_value,
                modality=raw.modality,
                source_scene_id=scene_id,
                source_start=raw.source_start,
                source_end=raw.source_end,
                source_candidate_id=cand.id,
                confirmed=True,
                auto_confirmed=True,
            )
            session.add(canon)
            auto_confirmed_count += 1

    session.commit()

    pending_count = len(created_candidates) - auto_confirmed_count
    return {
        "scene_id": scene_id,
        "candidate_count": len(created_candidates),
        "auto_confirmed_count": auto_confirmed_count,
        "pending_review_count": pending_count,
        "candidates": [
            {
                "id": c.id,
                "subject": c.subject,
                "predicate": c.predicate,
                "object_value": c.object_value,
                "modality": c.modality,
                "cognitive_subject": c.cognitive_subject,
                "source_start": c.source_start,
                "source_end": c.source_end,
                "source_text": c.source_text,
                "confidence": c.confidence,
                "entity_confidence": c.entity_confidence,
                "status": c.status,
            }
            for c in created_candidates
        ],
    }


def batch_extract_chapter_claims(
    session: Session,
    chapter_id: int,
    skip_auto_confirmed: bool = False,
) -> dict[str, Any]:
    chapter = session.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")

    scenes = list(session.scalars(select(Scene).where(Scene.chapter_id == chapter_id).order_by(Scene.sequence.asc())).all())
    total_candidates = 0
    total_auto = 0
    total_pending = 0
    results: list[dict[str, Any]] = []

    for scene in scenes:
        res = extract_scene_claims(session, scene.id, force_full_scan=True)
        total_candidates += res["candidate_count"]
        total_auto += res["auto_confirmed_count"]
        total_pending += res["pending_review_count"]
        results.append(res)

    return {
        "chapter_id": chapter_id,
        "scene_count": len(scenes),
        "candidate_count": total_candidates,
        "auto_confirmed_count": total_auto,
        "pending_review_count": total_pending,
        "scenes": results,
    }
