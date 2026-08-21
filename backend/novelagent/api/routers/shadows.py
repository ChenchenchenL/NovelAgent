from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import AppState, require_session
from ...application.services import project_service, shadow_identity_service
from ..schemas.continuity import (
    IdentityHypothesisCreate,
    IdentityHypothesisView,
    IdentityRevealRequest,
    IdentityRevealView,
    ShadowEntityCreate,
    ShadowEntityView,
)

router = APIRouter(tags=["Shadow Entities & Reveal"])


@router.get("/api/shadow-entities", response_model=list[ShadowEntityView])
def list_shadow_entities_endpoint(state: AppState = Depends(require_session)) -> list[ShadowEntityView]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        entities = shadow_identity_service.list_shadow_entities(db, project.id)
        return [
            ShadowEntityView(
                id=s.id,
                project_id=s.project_id,
                display_name=s.display_name,
                canonical_character=s.canonical_character,
                canonical_character_id=s.canonical_character_id,
                revealed_scene_id=s.revealed_scene_id,
                revealed=s.revealed,
            )
            for s in entities
        ]


@router.post("/api/shadow-entities", response_model=ShadowEntityView)
def create_shadow_entity_endpoint(
    payload: ShadowEntityCreate, state: AppState = Depends(require_session)
) -> ShadowEntityView:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        s = shadow_identity_service.create_shadow_entity(db, project.id, payload.display_name)
        return ShadowEntityView(
            id=s.id,
            project_id=s.project_id,
            display_name=s.display_name,
            canonical_character=s.canonical_character,
            canonical_character_id=s.canonical_character_id,
            revealed_scene_id=s.revealed_scene_id,
            revealed=s.revealed,
        )


@router.get("/api/shadow-entities/{shadow_id}", response_model=ShadowEntityView)
def get_shadow_entity_endpoint(shadow_id: int, state: AppState = Depends(require_session)) -> ShadowEntityView:
    _, factory = state.require_project()
    with factory() as db:
        try:
            s = shadow_identity_service.get_shadow_entity(db, shadow_id)
            return ShadowEntityView(
                id=s.id,
                project_id=s.project_id,
                display_name=s.display_name,
                canonical_character=s.canonical_character,
                canonical_character_id=s.canonical_character_id,
                revealed_scene_id=s.revealed_scene_id,
                revealed=s.revealed,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))


@router.post("/api/shadow-entities/{shadow_id}/hypotheses", response_model=IdentityHypothesisView)
def create_identity_hypothesis_endpoint(
    shadow_id: int, payload: IdentityHypothesisCreate, state: AppState = Depends(require_session)
) -> IdentityHypothesisView:
    _, factory = state.require_project()
    with factory() as db:
        try:
            h = shadow_identity_service.create_identity_hypothesis(
                db,
                shadow_id,
                payload.canonical_character_id,
                payload.evidence,
                payload.confidence,
                payload.earliest_reveal_scene_id,
                payload.confirmed,
            )
            return IdentityHypothesisView(
                id=h.id,
                shadow_entity_id=h.shadow_entity_id,
                canonical_character_id=h.canonical_character_id,
                evidence=h.evidence or [],
                confidence=h.confidence,
                earliest_reveal_scene_id=h.earliest_reveal_scene_id,
                confirmed=h.confirmed,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))


@router.post("/api/shadow-entities/{shadow_id}/reveal", response_model=IdentityRevealView)
def reveal_shadow_identity_endpoint(
    shadow_id: int, payload: IdentityRevealRequest, state: AppState = Depends(require_session)
) -> IdentityRevealView:
    _, factory = state.require_project()
    with factory() as db:
        try:
            r = shadow_identity_service.reveal_shadow_identity(
                db,
                shadow_id,
                payload.canonical_character_id,
                payload.reveal_scene_id,
                payload.evidence,
                payload.reader_visibility,
                payload.character_knowledge,
            )
            return IdentityRevealView(
                id=r.id,
                shadow_entity_id=r.shadow_entity_id,
                canonical_character_id=r.canonical_character_id,
                reveal_scene_id=r.reveal_scene_id,
                evidence=r.evidence,
                reader_visibility=r.reader_visibility,
                character_knowledge=r.character_knowledge or [],
                created_at=r.created_at.isoformat() if r.created_at else None,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))


@router.get("/api/shadow-entities/{shadow_id}/history")
def get_shadow_history_endpoint(shadow_id: int, state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        try:
            return shadow_identity_service.get_shadow_history(db, shadow_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
