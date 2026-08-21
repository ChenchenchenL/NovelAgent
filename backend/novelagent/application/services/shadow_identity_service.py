from __future__ import annotations

from typing import Any, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...domain.continuity_models import (
    Character,
    CharacterState,
    IdentityHypothesis,
    IdentityRevealEvent,
    MovementEvent,
)
from ...domain.models import ShadowEntity
from ...domain.rules import evaluate_shadow_coexistence


def create_shadow_entity(
    session: Session,
    project_id: int,
    display_name: str,
) -> ShadowEntity:
    shadow = ShadowEntity(
        project_id=project_id,
        display_name=display_name.strip(),
        revealed=False,
    )
    session.add(shadow)
    session.commit()
    session.refresh(shadow)
    return shadow


def get_shadow_entity(session: Session, shadow_id: int) -> ShadowEntity:
    shadow = session.get(ShadowEntity, shadow_id)
    if not shadow:
        raise KeyError(f"影子实体不存在: ID {shadow_id}")
    return shadow


def list_shadow_entities(session: Session, project_id: int) -> list[ShadowEntity]:
    stmt = select(ShadowEntity).where(ShadowEntity.project_id == project_id).order_by(ShadowEntity.id.asc())
    return list(session.scalars(stmt).all())


def create_identity_hypothesis(
    session: Session,
    shadow_id: int,
    canonical_character_id: int,
    evidence: list[dict[str, Any]] | None = None,
    confidence: float = 0.0,
    earliest_reveal_scene_id: int | None = None,
    confirmed: bool = False,
) -> IdentityHypothesis:
    get_shadow_entity(session, shadow_id)
    char = session.get(Character, canonical_character_id)
    if not char:
        raise KeyError(f"关联正典人物不存在: ID {canonical_character_id}")

    hyp = IdentityHypothesis(
        shadow_entity_id=shadow_id,
        canonical_character_id=canonical_character_id,
        evidence=evidence or [],
        confidence=confidence,
        earliest_reveal_scene_id=earliest_reveal_scene_id,
        confirmed=confirmed,
    )
    session.add(hyp)
    session.commit()
    session.refresh(hyp)
    return hyp


def reveal_shadow_identity(
    session: Session,
    shadow_id: int,
    canonical_character_id: int,
    reveal_scene_id: int,
    evidence: str | None = None,
    reader_visibility: str = "FULL",
    character_knowledge: list[dict[str, Any]] | None = None,
) -> IdentityRevealEvent:
    shadow = get_shadow_entity(session, shadow_id)
    canonical = session.get(Character, canonical_character_id)
    if not canonical:
        raise KeyError(f"关联正典人物不存在: ID {canonical_character_id}")

    # Gather shadow scene occurrences from hypotheses evidence
    hypotheses = list(
        session.scalars(select(IdentityHypothesis).where(IdentityHypothesis.shadow_entity_id == shadow_id)).all()
    )
    shadow_states: list[dict[str, Any]] = []
    for h in hypotheses:
        for ev in (h.evidence or []):
            if isinstance(ev, dict) and "scene_id" in ev:
                shadow_states.append({
                    "scene_id": ev["scene_id"],
                    "location": ev.get("location"),
                })

    canonical_states = list(
        session.scalars(select(CharacterState).where(CharacterState.character_id == canonical_character_id)).all()
    )
    canonical_dicts = [{"scene_id": cs.scene_id, "location": cs.location} for cs in canonical_states]
    conflicts = evaluate_shadow_coexistence(shadow_states, canonical_dicts)
    if conflicts:
        raise ValueError(f"掉马冲突：检测到同一时间/场景下的物理冲突: {conflicts}")

    shadow.revealed = True
    shadow.canonical_character_id = canonical_character_id
    shadow.revealed_scene_id = reveal_scene_id

    reveal_evt = IdentityRevealEvent(
        shadow_entity_id=shadow_id,
        canonical_character_id=canonical_character_id,
        reveal_scene_id=reveal_scene_id,
        evidence=evidence,
        reader_visibility=reader_visibility,
        character_knowledge=character_knowledge or [],
    )
    session.add(reveal_evt)
    session.commit()
    session.refresh(reveal_evt)
    return reveal_evt


def get_shadow_history(session: Session, shadow_id: int) -> dict[str, Any]:
    shadow = get_shadow_entity(session, shadow_id)
    hypotheses = list(
        session.scalars(select(IdentityHypothesis).where(IdentityHypothesis.shadow_entity_id == shadow_id)).all()
    )
    reveal_events = list(
        session.scalars(select(IdentityRevealEvent).where(IdentityRevealEvent.shadow_entity_id == shadow_id)).all()
    )
    return {
        "shadow_entity": {
            "id": shadow.id,
            "project_id": shadow.project_id,
            "display_name": shadow.display_name,
            "canonical_character_id": shadow.canonical_character_id,
            "revealed_scene_id": shadow.revealed_scene_id,
            "revealed": shadow.revealed,
        },
        "hypotheses": [
            {
                "id": h.id,
                "shadow_entity_id": h.shadow_entity_id,
                "canonical_character_id": h.canonical_character_id,
                "evidence": h.evidence or [],
                "confidence": h.confidence,
                "earliest_reveal_scene_id": h.earliest_reveal_scene_id,
                "confirmed": h.confirmed,
            }
            for h in hypotheses
        ],
        "reveal_events": [
            {
                "id": r.id,
                "shadow_entity_id": r.shadow_entity_id,
                "canonical_character_id": r.canonical_character_id,
                "reveal_scene_id": r.reveal_scene_id,
                "evidence": r.evidence,
                "reader_visibility": r.reader_visibility,
                "character_knowledge": r.character_knowledge or [],
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in reveal_events
        ],
    }
