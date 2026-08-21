from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import AppState, require_session
from ...application.services import character_service, project_service
from ..schemas.continuity import (
    CharacterCreate,
    CharacterStateCreate,
    CharacterStateView,
    CharacterUpdate,
    CharacterView,
)

router = APIRouter(tags=["Characters"])


@router.get("/api/characters", response_model=list[CharacterView])
def list_characters_endpoint(state: AppState = Depends(require_session)) -> list[CharacterView]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        chars = character_service.list_characters(db, project.id)
        return [
            CharacterView(
                id=c.id,
                project_id=c.project_id,
                name=c.name,
                aliases=c.aliases or [],
                background=c.background,
                core_traits=c.core_traits or [],
                created_at=c.created_at.isoformat() if c.created_at else None,
            )
            for c in chars
        ]


@router.post("/api/characters", response_model=CharacterView)
def create_character_endpoint(payload: CharacterCreate, state: AppState = Depends(require_session)) -> CharacterView:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        c = character_service.create_character(
            db,
            project.id,
            payload.name,
            payload.aliases,
            payload.background,
            payload.core_traits,
        )
        return CharacterView(
            id=c.id,
            project_id=c.project_id,
            name=c.name,
            aliases=c.aliases or [],
            background=c.background,
            core_traits=c.core_traits or [],
            created_at=c.created_at.isoformat() if c.created_at else None,
        )


@router.get("/api/characters/{char_id}", response_model=CharacterView)
def get_character_endpoint(char_id: int, state: AppState = Depends(require_session)) -> CharacterView:
    _, factory = state.require_project()
    with factory() as db:
        try:
            c = character_service.get_character(db, char_id)
            return CharacterView(
                id=c.id,
                project_id=c.project_id,
                name=c.name,
                aliases=c.aliases or [],
                background=c.background,
                core_traits=c.core_traits or [],
                created_at=c.created_at.isoformat() if c.created_at else None,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))


@router.put("/api/characters/{char_id}", response_model=CharacterView)
def update_character_endpoint(
    char_id: int, payload: CharacterUpdate, state: AppState = Depends(require_session)
) -> CharacterView:
    _, factory = state.require_project()
    with factory() as db:
        try:
            c = character_service.update_character(
                db,
                char_id,
                payload.name,
                payload.aliases,
                payload.background,
                payload.core_traits,
            )
            return CharacterView(
                id=c.id,
                project_id=c.project_id,
                name=c.name,
                aliases=c.aliases or [],
                background=c.background,
                core_traits=c.core_traits or [],
                created_at=c.created_at.isoformat() if c.created_at else None,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/api/characters/{char_id}")
def delete_character_endpoint(char_id: int, state: AppState = Depends(require_session)) -> dict[str, bool]:
    _, factory = state.require_project()
    with factory() as db:
        try:
            character_service.delete_character(db, char_id)
            return {"ok": True}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))


@router.get("/api/characters/{char_id}/states", response_model=list[CharacterStateView])
def list_character_states_endpoint(char_id: int, state: AppState = Depends(require_session)) -> list[CharacterStateView]:
    _, factory = state.require_project()
    with factory() as db:
        try:
            states = character_service.list_character_states(db, char_id)
            return [
                CharacterStateView(
                    id=s.id,
                    character_id=s.character_id,
                    scene_id=s.scene_id,
                    narrative_time=s.narrative_time,
                    location=s.location,
                    physical_state=s.physical_state,
                    goal=s.goal,
                    faction=s.faction,
                    emotion=s.emotion,
                    arc_stage=s.arc_stage,
                    confirmed=s.confirmed,
                )
                for s in states
            ]
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))


@router.post("/api/characters/{char_id}/states", response_model=CharacterStateView)
def create_character_state_endpoint(
    char_id: int, payload: CharacterStateCreate, state: AppState = Depends(require_session)
) -> CharacterStateView:
    _, factory = state.require_project()
    with factory() as db:
        try:
            s = character_service.create_character_state(db, char_id, payload.model_dump())
            return CharacterStateView(
                id=s.id,
                character_id=s.character_id,
                scene_id=s.scene_id,
                narrative_time=s.narrative_time,
                location=s.location,
                physical_state=s.physical_state,
                goal=s.goal,
                faction=s.faction,
                emotion=s.emotion,
                arc_stage=s.arc_stage,
                confirmed=s.confirmed,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))


@router.get("/api/characters/{char_id}/knowledge")
def get_character_knowledge_endpoint(char_id: int, state: AppState = Depends(require_session)) -> list[dict[str, Any]]:
    _, factory = state.require_project()
    with factory() as db:
        try:
            return character_service.get_character_knowledge(db, char_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
