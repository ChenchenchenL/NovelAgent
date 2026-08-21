from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import AppState, require_session
from ...application.services import project_service, secret_service
from ..schemas.continuity import (
    KnowledgeCheckRequest,
    SecretCreate,
    SecretRevealRequest,
    SecretView,
)

router = APIRouter(tags=["Narrative Secrets"])


@router.get("/api/secrets", response_model=list[SecretView])
def list_secrets_endpoint(state: AppState = Depends(require_session)) -> list[SecretView]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        secrets = secret_service.list_secrets(db, project.id)
        return [
            SecretView(
                id=s.id,
                project_id=s.project_id,
                secret_name=s.secret_name,
                secret_content=s.secret_content,
                created_scene_id=s.created_scene_id,
                created_narrative_time=s.created_narrative_time,
                known_by=s.known_by or [],
            )
            for s in secrets
        ]


@router.post("/api/secrets", response_model=SecretView)
def create_secret_endpoint(payload: SecretCreate, state: AppState = Depends(require_session)) -> SecretView:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        s = secret_service.create_secret(
            db,
            project.id,
            payload.secret_name,
            payload.secret_content,
            payload.created_scene_id,
            payload.created_narrative_time,
            payload.known_by,
        )
        return SecretView(
            id=s.id,
            project_id=s.project_id,
            secret_name=s.secret_name,
            secret_content=s.secret_content,
            created_scene_id=s.created_scene_id,
            created_narrative_time=s.created_narrative_time,
            known_by=s.known_by or [],
        )


@router.get("/api/secrets/{secret_id}", response_model=SecretView)
def get_secret_endpoint(secret_id: int, state: AppState = Depends(require_session)) -> SecretView:
    _, factory = state.require_project()
    with factory() as db:
        try:
            s = secret_service.get_secret(db, secret_id)
            return SecretView(
                id=s.id,
                project_id=s.project_id,
                secret_name=s.secret_name,
                secret_content=s.secret_content,
                created_scene_id=s.created_scene_id,
                created_narrative_time=s.created_narrative_time,
                known_by=s.known_by or [],
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))


@router.post("/api/secrets/{secret_id}/reveal", response_model=SecretView)
def reveal_secret_endpoint(
    secret_id: int, payload: SecretRevealRequest, state: AppState = Depends(require_session)
) -> SecretView:
    _, factory = state.require_project()
    with factory() as db:
        try:
            s = secret_service.reveal_secret_to_character(
                db,
                secret_id,
                payload.character_id,
                payload.scene_id,
                payload.narrative_time,
            )
            return SecretView(
                id=s.id,
                project_id=s.project_id,
                secret_name=s.secret_name,
                secret_content=s.secret_content,
                created_scene_id=s.created_scene_id,
                created_narrative_time=s.created_narrative_time,
                known_by=s.known_by or [],
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/api/secrets/{secret_id}")
def delete_secret_endpoint(secret_id: int, state: AppState = Depends(require_session)) -> dict[str, bool]:
    _, factory = state.require_project()
    with factory() as db:
        try:
            secret_service.delete_secret(db, secret_id)
            return {"ok": True}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))


@router.post("/api/scenes/{scene_id}/check-knowledge")
def check_scene_knowledge_endpoint(
    scene_id: int, payload: KnowledgeCheckRequest, state: AppState = Depends(require_session)
) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        try:
            return secret_service.check_scene_knowledge_violations(
                db, project.id, scene_id, payload.character_id, payload.secret_ids
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
