from __future__ import annotations

from typing import Any, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...domain.continuity_models import NarrativeSecret
from ...domain.models import Scene
from ...domain.rules import check_character_knowledge_violation


def create_secret(
    session: Session,
    project_id: int,
    secret_name: str,
    secret_content: str,
    created_scene_id: int,
    created_narrative_time: str | None = None,
    known_by: list[dict[str, Any]] | None = None,
) -> NarrativeSecret:
    secret = NarrativeSecret(
        project_id=project_id,
        secret_name=secret_name.strip(),
        secret_content=secret_content,
        created_scene_id=created_scene_id,
        created_narrative_time=created_narrative_time,
        known_by=known_by or [],
    )
    session.add(secret)
    session.commit()
    session.refresh(secret)
    return secret


def get_secret(session: Session, secret_id: int) -> NarrativeSecret:
    sec = session.get(NarrativeSecret, secret_id)
    if not sec:
        raise KeyError(f"叙事秘密不存在: ID {secret_id}")
    return sec


def list_secrets(session: Session, project_id: int) -> list[NarrativeSecret]:
    stmt = select(NarrativeSecret).where(NarrativeSecret.project_id == project_id).order_by(NarrativeSecret.id.asc())
    return list(session.scalars(stmt).all())


def reveal_secret_to_character(
    session: Session,
    secret_id: int,
    character_id: int,
    scene_id: int,
    narrative_time: str | None = None,
) -> NarrativeSecret:
    sec = get_secret(session, secret_id)
    known = list(sec.known_by or [])
    if not any(k.get("character_id") == character_id for k in known):
        known.append({
            "character_id": character_id,
            "known_since_scene_id": scene_id,
            "known_since_time": narrative_time,
        })
        sec.known_by = known
        session.commit()
        session.refresh(sec)
    return sec


def delete_secret(session: Session, secret_id: int) -> None:
    sec = get_secret(session, secret_id)
    session.delete(sec)
    session.commit()


def check_scene_knowledge_violations(
    session: Session,
    project_id: int,
    scene_id: int,
    character_id: int,
    secret_ids: list[int],
) -> dict[str, Any]:
    scene = session.get(Scene, scene_id)
    if not scene:
        raise KeyError(f"场景不存在: ID {scene_id}")

    secrets = list(
        session.scalars(
            select(NarrativeSecret).where(NarrativeSecret.project_id == project_id)
        ).all()
    )
    known_secret_ids = set()
    for s in secrets:
        for k in (s.known_by or []):
            if k.get("character_id") == character_id:
                known_secret_ids.add(s.id)

    violations = check_character_knowledge_violation(character_id, known_secret_ids, secret_ids)
    return {
        "scene_id": scene_id,
        "character_id": character_id,
        "violations_count": len(violations),
        "unauthorized_secret_ids": violations,
        "has_violation": len(violations) > 0,
    }
