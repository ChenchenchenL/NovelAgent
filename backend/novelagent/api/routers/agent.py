from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException

from ...application.services import (
    agent_director_service,
    autonomous_writer_service,
    project_service,
)
from ..dependencies import AppState, require_session
from ..schemas.agent import (
    AgentAutoAdvanceRequest,
    AgentAutoPlanRequest,
    AgentAutoPlanResponse,
    AgentAutoWriteRequest,
    AgentAutoWriteResponse,
    AgentDirectorChatRequest,
    AgentDirectorChatResponse,
)

router = APIRouter(tags=["agent"])


@router.post("/api/agent/auto-plan", response_model=AgentAutoPlanResponse)
def auto_plan_novel(
    req: AgentAutoPlanRequest,
    state: AppState = Depends(require_session),
) -> AgentAutoPlanResponse:
    _, factory = state.require_project()
    with factory() as db:
        proj = project_service.get_current_project(db)
        return agent_director_service.auto_plan_novel_outline(
            db,
            project_id=proj.id,
            seed_prompt=req.seed_prompt,
            genre=req.genre,
            target_volumes=req.target_volumes,
            chapters_per_vol=req.chapters_per_vol,
        )


@router.post("/api/agent/auto-write-scene", response_model=AgentAutoWriteResponse)
def auto_write_scene(
    req: AgentAutoWriteRequest,
    state: AppState = Depends(require_session),
) -> AgentAutoWriteResponse:
    _, factory = state.require_project()
    with factory() as db:
        proj = project_service.get_current_project(db)
        try:
            return autonomous_writer_service.auto_write_scene_grounded(
                db,
                project_id=proj.id,
                scene_id=req.scene_id,
                guidance=req.guidance,
                target_word_count=req.target_word_count,
                auto_extract=req.auto_extract,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))


@router.post("/api/agent/auto-advance", response_model=AgentAutoWriteResponse)
def auto_advance(
    req: AgentAutoAdvanceRequest | None = None,
    state: AppState = Depends(require_session),
) -> AgentAutoWriteResponse:
    _, factory = state.require_project()
    with factory() as db:
        proj = project_service.get_current_project(db)
        try:
            return autonomous_writer_service.auto_advance_next_scene(db, proj.id)
        except KeyError as exc:
            raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/agent/director-chat", response_model=AgentDirectorChatResponse)
def director_chat(
    req: AgentDirectorChatRequest,
    state: AppState = Depends(require_session),
) -> AgentDirectorChatResponse:
    _, factory = state.require_project()
    with factory() as db:
        proj = project_service.get_current_project(db)
        return agent_director_service.director_chat_interaction(
            db,
            project_id=proj.id,
            instruction=req.instruction,
            current_scene_id=req.current_scene_id,
        )
