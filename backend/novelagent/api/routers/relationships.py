from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import AppState, require_session
from ...application.services import project_service, relationship_service
from ..schemas.continuity import (
    RelationshipEventCreate,
    RelationshipEventView,
    RelationshipStateView,
)

router = APIRouter(tags=["Relationships"])


@router.get("/api/relationships", response_model=list[RelationshipEventView])
def list_relationships_endpoint(
    character_id: int | None = None, state: AppState = Depends(require_session)
) -> list[RelationshipEventView]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        events = relationship_service.list_relationship_events(db, project.id, character_id)
        return [
            RelationshipEventView(
                id=e.id,
                project_id=e.project_id,
                subject_character_id=e.subject_character_id,
                object_character_id=e.object_character_id,
                relationship_type=e.relationship_type,
                scene_id=e.scene_id,
                narrative_time=e.narrative_time,
                evidence=e.evidence,
                confirmed=e.confirmed,
                created_at=e.created_at.isoformat() if e.created_at else None,
            )
            for e in events
        ]


@router.post("/api/relationships", response_model=RelationshipEventView)
def create_relationship_endpoint(
    payload: RelationshipEventCreate, state: AppState = Depends(require_session)
) -> RelationshipEventView:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        try:
            e = relationship_service.create_relationship_event(
                db,
                project.id,
                payload.subject_character_id,
                payload.object_character_id,
                payload.relationship_type,
                payload.scene_id,
                payload.narrative_time,
                payload.evidence,
                payload.confirmed,
            )
            return RelationshipEventView(
                id=e.id,
                project_id=e.project_id,
                subject_character_id=e.subject_character_id,
                object_character_id=e.object_character_id,
                relationship_type=e.relationship_type,
                scene_id=e.scene_id,
                narrative_time=e.narrative_time,
                evidence=e.evidence,
                confirmed=e.confirmed,
                created_at=e.created_at.isoformat() if e.created_at else None,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))


@router.get("/api/characters/{char_id}/relationships", response_model=list[RelationshipEventView])
def get_character_relationships_endpoint(
    char_id: int, state: AppState = Depends(require_session)
) -> list[RelationshipEventView]:
    return list_relationships_endpoint(character_id=char_id, state=state)


@router.get("/api/relationships/current", response_model=list[RelationshipStateView])
def get_current_relationships_endpoint(
    character_id: int | None = None, state: AppState = Depends(require_session)
) -> list[RelationshipStateView]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        states = relationship_service.get_current_relationship_states(db, project.id, character_id)
        return [
            RelationshipStateView(
                id=s.id,
                project_id=s.project_id,
                subject_character_id=s.subject_character_id,
                object_character_id=s.object_character_id,
                relationship_type=s.relationship_type,
                as_of_scene_id=s.as_of_scene_id,
                as_of_narrative_time=s.as_of_narrative_time,
                updated_at=s.updated_at.isoformat() if s.updated_at else None,
            )
            for s in states
        ]
