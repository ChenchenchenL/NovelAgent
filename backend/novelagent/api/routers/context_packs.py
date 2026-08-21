from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import AppState, require_session
from ...application.services import context_pack_service, project_service
from ..schemas.search import ContextPackAssembleRequest, ContextPackValidateRequest

router = APIRouter(tags=["ContextPacks"])


@router.post("/api/context-packs")
def assemble_context_pack_endpoint(
    payload: ContextPackAssembleRequest,
    state: AppState = Depends(require_session),
) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        try:
            return context_pack_service.assemble_context_pack(
                db,
                project_id=project.id,
                scene_id=payload.scene_id,
                instruction=payload.instruction,
                selection=payload.selection,
                max_tokens=payload.max_tokens,
                include_kg_paths=payload.include_kg_paths,
                include_community_summaries=payload.include_community_summaries,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))


@router.post("/api/context-packs/validate")
def validate_context_pack_endpoint(
    payload: ContextPackValidateRequest,
    state: AppState = Depends(require_session),
) -> dict[str, Any]:
    return context_pack_service.validate_context_pack(payload.pack_data)
