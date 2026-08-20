from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from ..dependencies import AppState, get_scene_content, require_session
from ..schemas import ClaimDecision, ClaimView
from ...application.services import project_service, scene_service
from ...domain.models import CanonClaim, ClaimCandidate
from ...integrations.extraction import extract_candidates

router = APIRouter(tags=["Claims"])


@router.post("/api/scenes/{scene_id}/extract", response_model=list[ClaimView])
def extract(scene_id: int, state: AppState = Depends(require_session)) -> list[ClaimCandidate]:
    _, factory = state.require_project()
    with factory() as db:
        scene = scene_service.get_scene(db, scene_id)
        candidates = extract_candidates(get_scene_content(db, scene), aliases=set())
        created: list[ClaimCandidate] = []
        for c in candidates:
            row = ClaimCandidate(
                scene_id=scene.id,
                subject=c.subject,
                predicate=c.predicate,
                object_value=c.object_value,
                modality=c.modality,
                source_start=c.source_start,
                source_end=c.source_end,
                source_text=c.source_text,
                confidence=c.confidence,
                entity_confidence=c.entity_confidence,
                status=c.status,
            )
            db.add(row)
            created.append(row)
        db.commit()
        for r in created:
            db.refresh(r)
        return created


@router.get("/api/scenes/{scene_id}/claims", response_model=list[ClaimView])
def list_claims(scene_id: int, state: AppState = Depends(require_session)) -> list[ClaimCandidate]:
    _, factory = state.require_project()
    with factory() as db:
        return list(db.scalars(
            select(ClaimCandidate).where(ClaimCandidate.scene_id == scene_id).order_by(ClaimCandidate.id.desc())
        ).all())


@router.post("/api/claims/{claim_id}/decision")
def decide_claim(claim_id: int, payload: ClaimDecision, state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        claim = db.get(ClaimCandidate, claim_id)
        if not claim:
            raise HTTPException(status_code=404, detail="候选不存在")
        if payload.decision == "CONFIRM":
            claim.status = "CONFIRMED"
            project = project_service.get_current_project(db)
            canon = CanonClaim(
                project_id=project.id,
                subject=claim.subject,
                predicate=claim.predicate,
                object_value=claim.object_value,
                modality=claim.modality,
                source_scene_id=claim.scene_id,
                source_start=claim.source_start,
                source_end=claim.source_end,
                confirmed=True,
            )
            db.add(canon)
        elif payload.decision == "REJECT":
            claim.status = "REJECTED"
        else:
            claim.status = "DEFERRED"
        db.commit()
        return {"id": claim.id, "status": claim.status}
