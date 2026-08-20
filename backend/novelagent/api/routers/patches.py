from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from ..dependencies import AppState, require_session
from ..schemas import (
    PatchApplyResponse,
    PatchesMergeRequest,
    PatchesSelectiveAcceptRequest,
    RevisionDiffView,
    TextPatch,
)
from ...application.services import patch_service

router = APIRouter(tags=["Patches"])


@router.post("/api/scenes/{scene_id}/text-patches", response_model=PatchApplyResponse)
def apply_text_patch(scene_id: int, payload: TextPatch, state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        revision, applied_range = patch_service.apply_text_patch(db, scene_id, payload)
        return {
            "revision_id": revision.id,
            "status": "DRAFT",
            "applied_range": applied_range,
        }


@router.post("/api/scenes/{scene_id}/patches/merge")
def merge_patches(scene_id: int, payload: PatchesMergeRequest, state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        return patch_service.merge_text_patches(
            db, scene_id, payload.base_revision_id, payload.patches
        )


@router.post("/api/scenes/{scene_id}/patches/selective-accept")
def selective_accept(
    scene_id: int,
    payload: PatchesSelectiveAcceptRequest,
    state: AppState = Depends(require_session),
) -> dict[str, Any]:
    project_dir, factory = state.require_project()
    with factory() as db:
        scene, revision = patch_service.selective_accept_patches(
            db, project_dir, scene_id, payload.base_revision_id, payload.patches
        )
        return {
            "scene_id": scene.id,
            "revision_id": revision.id,
            "status": scene.status,
        }


@router.get("/api/scenes/{scene_id}/revisions/{revision_id}/diff", response_model=RevisionDiffView)
def get_revision_diff(
    scene_id: int,
    revision_id: int,
    against: int | None = Query(None, description="Base revision ID to compare against"),
    state: AppState = Depends(require_session),
) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        return patch_service.compute_revision_diff(db, scene_id, revision_id, against)
