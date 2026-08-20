from __future__ import annotations

import asyncio
from typing import Any, AsyncIterator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from ..dependencies import (
    AppState,
    append_event,
    get_app_state,
    get_scene_content,
    require_session,
)
from ..schemas import (
    ClaimDecision,
    GenerateRequest,
    PatchCreate,
    SceneCreate,
    SceneEntryContractUpdate,
    SceneExitStateUpdate,
    SceneStatusUpdate,
    SceneUpdate,
)
from ...application.services import project_service, scene_service
from ...domain.models import (
    CanonClaim,
    ClaimCandidate,
    GenerationRun,
    ItemEntity,
    ModelInvocation,
    ShadowEntity,
)
from ...infrastructure.fsck import check_project
from ...integrations.extraction import extract_candidates

router = APIRouter(tags=["Scenes"])


@router.post("/api/chapters/{chapter_id}/scenes")
def create_scene(chapter_id: int, payload: SceneCreate, state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        scene = scene_service.create_scene(
            db,
            project_id=project.id,
            chapter_id=chapter_id,
            title=payload.title,
            pov=payload.pov,
            location=payload.location,
        )
        return {
            "id": scene.id,
            "chapter_id": scene.chapter_id,
            "title": scene.title,
            "sequence": scene.sequence,
            "pov": scene.pov,
            "location": scene.location,
            "status": scene.status,
            "current_revision_id": scene.current_revision_id,
            "content": "",
            "entry_contract": scene.entry_contract,
            "exit_state": scene.exit_state,
        }


@router.get("/api/scenes/{scene_id}")
def get_scene(scene_id: int, state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        scene = scene_service.get_scene(db, scene_id)
        return {
            "id": scene.id,
            "chapter_id": scene.chapter_id,
            "title": scene.title,
            "sequence": scene.sequence,
            "pov": scene.pov,
            "location": scene.location,
            "status": scene.status,
            "current_revision_id": scene.current_revision_id,
            "content": get_scene_content(db, scene),
            "entry_contract": scene.entry_contract,
            "exit_state": scene.exit_state,
        }


@router.put("/api/scenes/{scene_id}")
def update_scene(scene_id: int, payload: SceneUpdate, state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        scene = scene_service.update_scene(db, scene_id, payload.title, payload.pov, payload.location)
        return {
            "id": scene.id,
            "chapter_id": scene.chapter_id,
            "title": scene.title,
            "sequence": scene.sequence,
            "pov": scene.pov,
            "location": scene.location,
            "status": scene.status,
            "current_revision_id": scene.current_revision_id,
            "content": get_scene_content(db, scene),
            "entry_contract": scene.entry_contract,
            "exit_state": scene.exit_state,
        }


@router.post("/api/scenes/{scene_id}/status")
def update_scene_status(scene_id: int, payload: SceneStatusUpdate, state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        scene = scene_service.change_scene_status(db, scene_id, payload.status)
        return {"id": scene.id, "status": scene.status}


@router.post("/api/scenes/{scene_id}/patches")
def create_patch(scene_id: int, payload: PatchCreate, state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        revision = scene_service.create_patch(
            db,
            scene_id=scene_id,
            base_revision_id=payload.base_revision_id,
            content=payload.content,
            source=payload.source,
        )
        return {"revision_id": revision.id, "status": "DRAFT"}


@router.post("/api/scenes/{scene_id}/revisions/{revision_id}/accept")
def accept_revision(scene_id: int, revision_id: int, state: AppState = Depends(require_session)) -> dict[str, Any]:
    project_dir, factory = state.require_project()
    with factory() as db:
        scene, revision = scene_service.accept_revision(db, project_dir, scene_id, revision_id)
        return {"scene_id": scene.id, "revision_id": revision.id, "status": scene.status}


@router.get("/api/scenes/{scene_id}/revisions")
def list_revisions(scene_id: int, state: AppState = Depends(require_session)) -> list[dict[str, Any]]:
    _, factory = state.require_project()
    with factory() as db:
        rows = scene_service.list_revisions(db, scene_id)
        return [
            {
                "id": r.id,
                "scene_id": r.scene_id,
                "base_revision_id": r.base_revision_id,
                "source": r.source,
                "content_hash": r.content_hash,
                "created_at": r.created_at.isoformat() if r.created_at else "",
            }
            for r in rows
        ]


@router.get("/api/scenes/{scene_id}/revisions/{revision_id}")
def get_revision(scene_id: int, revision_id: int, state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        r = scene_service.get_revision(db, scene_id, revision_id)
        return {
            "id": r.id,
            "scene_id": r.scene_id,
            "base_revision_id": r.base_revision_id,
            "content": r.content,
            "source": r.source,
            "content_hash": r.content_hash,
            "created_at": r.created_at.isoformat() if r.created_at else "",
        }


@router.put("/api/scenes/{scene_id}/entry-contract")
def update_entry_contract(scene_id: int, payload: SceneEntryContractUpdate, state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        scene = scene_service.update_entry_contract(db, scene_id, payload.entry_contract)
        return {"id": scene.id, "entry_contract": scene.entry_contract}


@router.put("/api/scenes/{scene_id}/exit-state")
def update_exit_state(scene_id: int, payload: SceneExitStateUpdate, state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        scene = scene_service.update_exit_state(db, scene_id, payload.exit_state)
        return {"id": scene.id, "exit_state": scene.exit_state}


@router.delete("/api/scenes/{scene_id}")
def delete_scene(scene_id: int, state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        deleted_id = scene_service.delete_scene(db, scene_id)
        return {"status": "ok", "deleted_scene_id": deleted_id}


@router.post("/api/scenes/{scene_id}/extract")
def extract(scene_id: int, state: AppState = Depends(require_session)) -> list[dict[str, Any]]:
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
        return [
            {
                "id": r.id,
                "subject": r.subject,
                "predicate": r.predicate,
                "object_value": r.object_value,
                "modality": r.modality,
                "source_start": r.source_start,
                "source_end": r.source_end,
                "source_text": r.source_text,
                "confidence": r.confidence,
                "entity_confidence": r.entity_confidence,
                "status": r.status,
            }
            for r in created
        ]


@router.get("/api/scenes/{scene_id}/claims")
def list_claims(scene_id: int, state: AppState = Depends(require_session)) -> list[dict[str, Any]]:
    _, factory = state.require_project()
    with factory() as db:
        rows = db.scalars(
            select(ClaimCandidate).where(ClaimCandidate.scene_id == scene_id).order_by(ClaimCandidate.id.desc())
        ).all()
        return [
            {
                "id": r.id,
                "subject": r.subject,
                "predicate": r.predicate,
                "object_value": r.object_value,
                "modality": r.modality,
                "source_start": r.source_start,
                "source_end": r.source_end,
                "source_text": r.source_text,
                "confidence": r.confidence,
                "entity_confidence": r.entity_confidence,
                "status": r.status,
            }
            for r in rows
        ]


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


@router.post("/api/scenes/{scene_id}/generate")
async def generate(scene_id: int, payload: GenerateRequest, state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        scene = scene_service.get_scene(db, scene_id)
        run = GenerationRun(scene_id=scene.id, prompt=payload.instruction, status="RUNNING")
        invocation = ModelInvocation(
            task_type="scene_generation",
            tier=payload.tier,
            model=state.model_config.models.get(payload.tier, "adapter-mock"),
            status="RUNNING",
        )
        db.add(run)
        db.add(invocation)
        db.commit()
        db.refresh(run)

    append_event(state, run.id, "started", f"Run #{run.id} started on tier {payload.tier}")

    async def _runner() -> None:
        await asyncio.sleep(0.05)
        append_event(state, run.id, "delta", "【Agent 生成片段】林舟按住剑柄，缓步推开客栈后门。")
        append_event(state, run.id, "completed", "生成完成")

    asyncio.create_task(_runner())
    return {"run_id": run.id, "status": "RUNNING"}


@router.get("/api/generation-runs/{run_id}/events")
async def generation_events(run_id: int, state: AppState = Depends(get_app_state)) -> StreamingResponse:
    async def _stream() -> AsyncIterator[str]:
        cursor = 0
        while True:
            with state.event_lock:
                current_events = list(state.events.get(run_id, []))
            while cursor < len(current_events):
                ev = current_events[cursor]
                cursor += 1
                yield f"event: {ev['event']}\ndata: {ev['data']}\n\n"
                if ev["event"] in {"completed", "failed"}:
                    return
            await asyncio.sleep(0.1)

    return StreamingResponse(_stream(), media_type="text/event-stream")


@router.get("/api/items")
def list_items(state: AppState = Depends(require_session)) -> list[dict[str, Any]]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        items = db.scalars(select(ItemEntity).where(ItemEntity.project_id == project.id)).all()
        return [{"id": i.id, "name": i.name, "current_holder": i.current_holder, "state": i.current_state} for i in items]


@router.get("/api/shadow-entities")
def list_shadow_entities(state: AppState = Depends(require_session)) -> list[dict[str, Any]]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        entities = db.scalars(select(ShadowEntity).where(ShadowEntity.project_id == project.id)).all()
        return [{"id": s.id, "name": s.display_name, "canonical": s.canonical_character} for s in entities]


@router.post("/api/fsck")
def run_fsck(state: AppState = Depends(require_session)) -> dict[str, Any]:
    project_dir, factory = state.require_project()
    with factory() as session:
        return check_project(project_dir, session)
