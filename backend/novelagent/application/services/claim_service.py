from __future__ import annotations

import logging
from typing import Any

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ...domain.models import CanonClaim, Chapter, ClaimCandidate, EntityAlias, Scene

logger = logging.getLogger(__name__)


def list_candidates(
    session: Session,
    scene_id: int,
    status: str | None = None,
    modality: str | None = None,
) -> list[ClaimCandidate]:
    stmt = select(ClaimCandidate).where(ClaimCandidate.scene_id == scene_id)
    if status:
        stmt = stmt.where(ClaimCandidate.status == status)
    if modality:
        stmt = stmt.where(ClaimCandidate.modality == modality)
    stmt = stmt.order_by(ClaimCandidate.id.asc())
    return list(session.scalars(stmt).all())


def list_canon_claims(
    session: Session,
    scene_id: int | None = None,
    project_id: int | None = None,
) -> list[CanonClaim]:
    stmt = select(CanonClaim)
    if scene_id is not None:
        stmt = stmt.where(CanonClaim.source_scene_id == scene_id)
    if project_id is not None:
        stmt = stmt.where(CanonClaim.project_id == project_id)
    stmt = stmt.order_by(CanonClaim.id.desc())
    return list(session.scalars(stmt).all())


def submit_decision(
    session: Session,
    candidate_id: int,
    decision: str,
    corrections: dict[str, Any] | None = None,
    notes: str | None = None,
) -> tuple[ClaimCandidate, CanonClaim | None]:
    cand = session.get(ClaimCandidate, candidate_id)
    if not cand:
        raise HTTPException(status_code=404, detail="候选主张不存在")

    created_canon: CanonClaim | None = None

    if decision == "CONFIRM":
        cand.status = "CONFIRMED"
        # Apply manual corrections
        if corrections:
            cand.subject = corrections.get("subject", cand.subject)
            cand.predicate = corrections.get("predicate", cand.predicate)
            cand.object_value = corrections.get("object_value", cand.object_value)
            cand.modality = corrections.get("modality", cand.modality)
            if "cognitive_subject" in corrections:
                cand.cognitive_subject = corrections["cognitive_subject"]

        scene = session.get(Scene, cand.scene_id)
        chapter = session.get(Chapter, scene.chapter_id) if scene else None
        proj_id = chapter.project_id if chapter else 1

        created_canon = CanonClaim(
            project_id=proj_id,
            subject=cand.subject,
            predicate=cand.predicate,
            object_value=cand.object_value,
            modality=cand.modality,
            source_scene_id=cand.scene_id,
            source_start=cand.source_start,
            source_end=cand.source_end,
            source_candidate_id=cand.id,
            confirmed=True,
            auto_confirmed=False,
            author_decision_notes=notes,
        )
        session.add(created_canon)

    elif decision == "REJECT":
        cand.status = "REJECTED"
    elif decision == "DEFER":
        cand.status = "DEFERRED"
    else:
        raise HTTPException(status_code=400, detail=f"未知裁决动作: {decision}")

    session.commit()
    session.refresh(cand)
    if created_canon:
        session.refresh(created_canon)
    return cand, created_canon


def submit_batch_decisions(
    session: Session,
    scene_id: int,
    decisions: list[dict[str, Any]],
) -> dict[str, Any]:
    confirmed_count = 0
    rejected_count = 0
    deferred_count = 0
    created_canons: list[dict[str, Any]] = []

    for item in decisions:
        c_id = item.get("id")
        dec = item.get("decision", "CONFIRM")
        corrs = item.get("corrections")
        notes = item.get("notes") or item.get("rejection_reason")
        if not c_id:
            continue

        cand, canon = submit_decision(session, c_id, dec, corrections=corrs, notes=notes)
        if dec == "CONFIRM":
            confirmed_count += 1
            if canon:
                created_canons.append({"id": canon.id, "subject": canon.subject, "predicate": canon.predicate, "object_value": canon.object_value})
        elif dec == "REJECT":
            rejected_count += 1
        elif dec == "DEFER":
            deferred_count += 1

    conflicts = check_conflicts(session, project_id=1, scene_id=scene_id)
    return {
        "confirmed_count": confirmed_count,
        "rejected_count": rejected_count,
        "deferred_count": deferred_count,
        "created_canon_claims": created_canons,
        "conflicts_detected": conflicts,
    }


def check_conflicts(
    session: Session,
    project_id: int,
    scene_id: int | None = None,
) -> list[dict[str, Any]]:
    """Detect hard logical conflicts across confirmed ACTUAL canon claims."""
    stmt = select(CanonClaim).where(CanonClaim.confirmed.is_(True), CanonClaim.modality == "ACTUAL")
    if scene_id is not None:
        stmt = stmt.where(CanonClaim.source_scene_id == scene_id)
    claims = list(session.scalars(stmt).all())

    conflicts: list[dict[str, Any]] = []
    # Check 1: Unique item hold conflicts (two characters claiming to hold the same item in the same scene)
    item_holders: dict[str, list[CanonClaim]] = {}
    for c in claims:
        if c.predicate == "holds":
            item_holders.setdefault(c.object_value, []).append(c)

    for item_name, holder_claims in item_holders.items():
        if len(holder_claims) > 1:
            distinct_subjs = {h.subject for h in holder_claims}
            if len(distinct_subjs) > 1:
                conflicts.append({
                    "id": f"conflict_holds_{item_name}",
                    "severity": "BLOCKING_CONFIRMED",
                    "left_claim": {"id": holder_claims[0].id, "subject": holder_claims[0].subject, "predicate": "holds", "object_value": item_name},
                    "right_claim": {"id": holder_claims[1].id, "subject": holder_claims[1].subject, "predicate": "holds", "object_value": item_name},
                    "message": f"物品 [{item_name}] 在同一场景中被多位人物 ({', '.join(distinct_subjs)}) 同时持有",
                    "resolution_options": ["修改持有者", "将其中一条改为 DEFERRED", "添加转移事件"],
                })

    return conflicts


def list_aliases(session: Session, project_id: int) -> list[EntityAlias]:
    return list(session.scalars(select(EntityAlias).where(EntityAlias.project_id == project_id).order_by(EntityAlias.canonical_name.asc())).all())


def create_alias(
    session: Session,
    project_id: int,
    canonical_name: str,
    alias_name: str,
    alias_type: str = "informal",
    confirmed_by: bool = True,
) -> EntityAlias:
    existing = session.scalar(
        select(EntityAlias).where(
            EntityAlias.project_id == project_id,
            EntityAlias.canonical_name == canonical_name,
            EntityAlias.alias_name == alias_name,
        )
    )
    if existing:
        existing.alias_type = alias_type
        existing.confirmed_by = confirmed_by
        session.commit()
        session.refresh(existing)
        return existing

    alias = EntityAlias(
        project_id=project_id,
        canonical_name=canonical_name,
        alias_name=alias_name,
        alias_type=alias_type,
        confirmed_by=confirmed_by,
    )
    session.add(alias)
    session.commit()
    session.refresh(alias)
    return alias


def delete_alias(session: Session, alias_id: int) -> None:
    alias = session.get(EntityAlias, alias_id)
    if not alias:
        raise HTTPException(status_code=404, detail="别名记录不存在")
    session.delete(alias)
    session.commit()
