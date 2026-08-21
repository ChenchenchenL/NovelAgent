from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from ..dependencies import AppState, require_session
from ..schemas import (
    BatchClaimDecisionRequest,
    CanonClaimView,
    ClaimDecision,
    ClaimExtractRequest,
    ClaimView,
    EntityAliasCreate,
    EntityAliasView,
)
from ...application.services import claim_service, extraction_service

router = APIRouter(tags=["Claims"])


@router.post("/api/scenes/{scene_id}/extract")
def extract_scene(
    scene_id: int,
    payload: ClaimExtractRequest | None = None,
    state: AppState = Depends(require_session),
) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        rev_id = payload.revision_id if payload else None
        force = payload.force_full_scan if payload else False
        return extraction_service.extract_scene_claims(
            session=db,
            scene_id=scene_id,
            revision_id=rev_id,
            force_full_scan=force,
        )


@router.post("/api/chapters/{chapter_id}/batch-extract")
def batch_extract_chapter(
    chapter_id: int,
    state: AppState = Depends(require_session),
) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        return extraction_service.batch_extract_chapter_claims(db, chapter_id)


@router.get("/api/scenes/{scene_id}/claim-candidates", response_model=list[ClaimView])
@router.get("/api/scenes/{scene_id}/claims", response_model=list[ClaimView])
def list_candidates(
    scene_id: int,
    status: str | None = Query(default=None),
    modality: str | None = Query(default=None),
    state: AppState = Depends(require_session),
) -> list[dict[str, Any]]:
    _, factory = state.require_project()
    with factory() as db:
        items = claim_service.list_candidates(db, scene_id, status=status, modality=modality)
        return [
            {
                "id": c.id,
                "subject": c.subject,
                "predicate": c.predicate,
                "object_value": c.object_value,
                "modality": c.modality,
                "cognitive_subject": c.cognitive_subject,
                "source_start": c.source_start,
                "source_end": c.source_end,
                "paragraph_index": c.paragraph_index,
                "source_text": c.source_text,
                "confidence": c.confidence,
                "entity_confidence": c.entity_confidence,
                "status": c.status,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in items
        ]


@router.get("/api/scenes/{scene_id}/canon-claims", response_model=list[CanonClaimView])
def list_canon_claims(
    scene_id: int,
    state: AppState = Depends(require_session),
) -> list[dict[str, Any]]:
    _, factory = state.require_project()
    with factory() as db:
        items = claim_service.list_canon_claims(db, scene_id=scene_id)
        return [
            {
                "id": c.id,
                "project_id": c.project_id,
                "subject": c.subject,
                "predicate": c.predicate,
                "object_value": c.object_value,
                "modality": c.modality,
                "source_scene_id": c.source_scene_id,
                "source_start": c.source_start,
                "source_end": c.source_end,
                "source_candidate_id": c.source_candidate_id,
                "confirmed": c.confirmed,
                "auto_confirmed": c.auto_confirmed,
                "author_decision_notes": c.author_decision_notes,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            }
            for c in items
        ]


@router.post("/api/scenes/{scene_id}/claim-candidates/batch-decision")
def batch_decide_claims(
    scene_id: int,
    payload: BatchClaimDecisionRequest,
    state: AppState = Depends(require_session),
) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        return claim_service.submit_batch_decisions(db, scene_id, payload.decisions)


@router.post("/api/claim-candidates/{candidate_id}/decision")
@router.post("/api/claims/{candidate_id}/decision")
def decide_single_claim(
    candidate_id: int,
    payload: ClaimDecision,
    state: AppState = Depends(require_session),
) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        cand, canon = claim_service.submit_decision(
            session=db,
            candidate_id=candidate_id,
            decision=payload.decision,
            corrections=payload.corrections,
            notes=payload.notes,
        )
        return {
            "id": cand.id,
            "status": cand.status,
            "canon_claim_id": canon.id if canon else None,
        }


@router.get("/api/claims/conflicts")
def get_claim_conflicts(
    scene_id: int | None = Query(default=None),
    state: AppState = Depends(require_session),
) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        conflicts = claim_service.check_conflicts(db, project_id=1, scene_id=scene_id)
        return {"conflicts": conflicts}


@router.get("/api/entity-aliases", response_model=list[EntityAliasView])
def get_entity_aliases(state: AppState = Depends(require_session)) -> list[dict[str, Any]]:
    _, factory = state.require_project()
    with factory() as db:
        aliases = claim_service.list_aliases(db, project_id=1)
        return [
            {
                "id": a.id,
                "project_id": a.project_id,
                "canonical_name": a.canonical_name,
                "alias_name": a.alias_name,
                "alias_type": a.alias_type,
                "confirmed_by": a.confirmed_by,
                "created_at": a.created_at.isoformat() if a.created_at else "",
            }
            for a in aliases
        ]


@router.post("/api/entity-aliases", response_model=EntityAliasView)
def create_entity_alias(
    payload: EntityAliasCreate,
    state: AppState = Depends(require_session),
) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        alias = claim_service.create_alias(
            session=db,
            project_id=1,
            canonical_name=payload.canonical_name,
            alias_name=payload.alias_name,
            alias_type=payload.alias_type,
            confirmed_by=payload.confirmed_by,
        )
        return {
            "id": alias.id,
            "project_id": alias.project_id,
            "canonical_name": alias.canonical_name,
            "alias_name": alias.alias_name,
            "alias_type": alias.alias_type,
            "confirmed_by": alias.confirmed_by,
            "created_at": alias.created_at.isoformat() if alias.created_at else "",
        }


@router.delete("/api/entity-aliases/{alias_id}")
def delete_entity_alias(alias_id: int, state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        claim_service.delete_alias(db, alias_id)
        return {"status": "ok", "message": "别名已删除"}
