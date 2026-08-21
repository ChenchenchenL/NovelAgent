from __future__ import annotations

from typing import Any, Optional
from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session

from ...domain.continuity_models import (
    Character,
    CharacterState,
    IdentityHypothesis,
    IdentityRevealEvent,
    InformationGap,
    NarrativeSecret,
    RelationshipEvent,
    RelationshipState,
)


def create_character(
    session: Session,
    project_id: int,
    name: str,
    aliases: list[str] | None = None,
    background: str | None = None,
    core_traits: list[str] | None = None,
) -> Character:
    char = Character(
        project_id=project_id,
        name=name.strip(),
        aliases=aliases or [],
        background=background,
        core_traits=core_traits or [],
    )
    session.add(char)
    session.commit()
    session.refresh(char)
    return char


def get_character(session: Session, character_id: int) -> Character:
    char = session.get(Character, character_id)
    if not char:
        raise KeyError(f"人物不存在: ID {character_id}")
    return char


def list_characters(session: Session, project_id: int) -> list[Character]:
    stmt = select(Character).where(Character.project_id == project_id).order_by(Character.id.asc())
    return list(session.scalars(stmt).all())


def update_character(
    session: Session,
    character_id: int,
    name: str | None = None,
    aliases: list[str] | None = None,
    background: str | None = None,
    core_traits: list[str] | None = None,
) -> Character:
    char = get_character(session, character_id)
    if name is not None:
        char.name = name.strip()
    if aliases is not None:
        char.aliases = aliases
    if background is not None:
        char.background = background
    if core_traits is not None:
        char.core_traits = core_traits
    session.commit()
    session.refresh(char)
    return char


def delete_character(session: Session, character_id: int) -> None:
    char = get_character(session, character_id)
    # Cascade cleanup associated domain records to prevent foreign key errors
    session.execute(delete(CharacterState).where(CharacterState.character_id == character_id))
    session.execute(
        delete(RelationshipEvent).where(
            or_(
                RelationshipEvent.subject_character_id == character_id,
                RelationshipEvent.object_character_id == character_id,
            )
        )
    )
    session.execute(
        delete(RelationshipState).where(
            or_(
                RelationshipState.subject_character_id == character_id,
                RelationshipState.object_character_id == character_id,
            )
        )
    )
    session.execute(delete(InformationGap).where(InformationGap.character_id == character_id))
    session.execute(delete(IdentityHypothesis).where(IdentityHypothesis.canonical_character_id == character_id))
    session.execute(delete(IdentityRevealEvent).where(IdentityRevealEvent.canonical_character_id == character_id))
    session.delete(char)
    session.commit()


def create_character_state(
    session: Session,
    character_id: int,
    state_payload: dict[str, Any],
) -> CharacterState:
    get_character(session, character_id)
    scene_id = state_payload.get("scene_id")
    if not scene_id:
        raise ValueError("场景 ID 为必填项")
    state = CharacterState(
        character_id=character_id,
        scene_id=scene_id,
        narrative_time=state_payload.get("narrative_time"),
        location=state_payload.get("location"),
        physical_state=state_payload.get("physical_state"),
        goal=state_payload.get("goal"),
        faction=state_payload.get("faction"),
        emotion=state_payload.get("emotion"),
        arc_stage=state_payload.get("arc_stage"),
        confirmed=state_payload.get("confirmed", False),
    )
    session.add(state)
    session.commit()
    session.refresh(state)
    return state


def list_character_states(session: Session, character_id: int) -> list[CharacterState]:
    get_character(session, character_id)
    stmt = select(CharacterState).where(CharacterState.character_id == character_id).order_by(CharacterState.id.asc())
    return list(session.scalars(stmt).all())


def get_character_knowledge(session: Session, character_id: int) -> list[dict[str, Any]]:
    char = get_character(session, character_id)
    secrets = list(session.scalars(select(NarrativeSecret).where(NarrativeSecret.project_id == char.project_id)).all())
    knowledge = []
    for s in secrets:
        known_entries = [entry for entry in (s.known_by or []) if entry.get("character_id") == character_id]
        if known_entries:
            knowledge.append({
                "secret_id": s.id,
                "secret_name": s.secret_name,
                "knows": True,
                "known_since_scene_id": known_entries[0].get("known_since_scene_id"),
                "known_since_time": known_entries[0].get("known_since_time"),
            })
    return knowledge
