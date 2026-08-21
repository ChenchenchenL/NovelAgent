from __future__ import annotations

from typing import Any, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...domain.continuity_models import Character, RelationshipEvent, RelationshipState


def create_relationship_event(
    session: Session,
    project_id: int,
    subject_character_id: int,
    object_character_id: int,
    relationship_type: str,
    scene_id: int,
    narrative_time: str | None = None,
    evidence: str | None = None,
    confirmed: bool = False,
) -> RelationshipEvent:
    if not session.get(Character, subject_character_id):
        raise KeyError(f"主体人物不存在: ID {subject_character_id}")
    if not session.get(Character, object_character_id):
        raise KeyError(f"客体人物不存在: ID {object_character_id}")

    evt = RelationshipEvent(
        project_id=project_id,
        subject_character_id=subject_character_id,
        object_character_id=object_character_id,
        relationship_type=relationship_type,
        scene_id=scene_id,
        narrative_time=narrative_time,
        evidence=evidence,
        confirmed=confirmed,
    )
    session.add(evt)
    session.flush()

    # Update or insert current RelationshipState projection
    state = session.scalar(
        select(RelationshipState).where(
            RelationshipState.project_id == project_id,
            RelationshipState.subject_character_id == subject_character_id,
            RelationshipState.object_character_id == object_character_id,
        )
    )
    if not state:
        state = RelationshipState(
            project_id=project_id,
            subject_character_id=subject_character_id,
            object_character_id=object_character_id,
            relationship_type=relationship_type,
            as_of_scene_id=scene_id,
            as_of_narrative_time=narrative_time,
        )
        session.add(state)
    else:
        state.relationship_type = relationship_type
        state.as_of_scene_id = scene_id
        state.as_of_narrative_time = narrative_time

    session.commit()
    session.refresh(evt)
    return evt


def list_relationship_events(
    session: Session,
    project_id: int,
    character_id: int | None = None,
) -> list[RelationshipEvent]:
    stmt = select(RelationshipEvent).where(RelationshipEvent.project_id == project_id)
    if character_id is not None:
        stmt = stmt.where(
            (RelationshipEvent.subject_character_id == character_id)
            | (RelationshipEvent.object_character_id == character_id)
        )
    stmt = stmt.order_by(RelationshipEvent.id.asc())
    return list(session.scalars(stmt).all())


def get_current_relationship_states(
    session: Session,
    project_id: int,
    character_id: int | None = None,
) -> list[RelationshipState]:
    stmt = select(RelationshipState).where(RelationshipState.project_id == project_id)
    if character_id is not None:
        stmt = stmt.where(
            (RelationshipState.subject_character_id == character_id)
            | (RelationshipState.object_character_id == character_id)
        )
    stmt = stmt.order_by(RelationshipState.id.asc())
    return list(session.scalars(stmt).all())
