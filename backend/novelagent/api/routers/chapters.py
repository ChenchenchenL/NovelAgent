from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from ..dependencies import AppState, get_scene_content, require_session
from ..schemas import (
    ChapterCreate,
    ChapterDetailView,
    ChapterStatusUpdate,
    ChapterUpdate,
    ChapterView,
)
from ...application.services import chapter_service, project_service

router = APIRouter(tags=["Chapters"])


@router.get("/api/projects/current/chapters", response_model=list[ChapterView])
def list_chapters(state: AppState = Depends(require_session)) -> list[dict[str, Any]]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        rows = chapter_service.list_chapters(db, project.id)
        return [
            {
                "id": c.id,
                "project_id": c.project_id,
                "volume_id": c.volume_id,
                "title": c.title,
                "sequence": c.sequence,
                "status": c.status,
                "contract": c.contract,
            }
            for c in rows
        ]


@router.post("/api/projects/current/chapters", response_model=ChapterView)
def create_chapter(payload: ChapterCreate, state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        chapter = chapter_service.create_chapter(
            db,
            project_id=project.id,
            title=payload.title,
            volume_id=payload.volume_id,
            status=payload.status or "IDEA",
            contract=payload.contract,
        )
        return {
            "id": chapter.id,
            "project_id": chapter.project_id,
            "volume_id": chapter.volume_id,
            "title": chapter.title,
            "sequence": chapter.sequence,
            "status": chapter.status,
            "contract": chapter.contract,
        }


@router.get("/api/chapters/{chapter_id}", response_model=ChapterDetailView)
def get_chapter(chapter_id: int, state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        chapter, scenes = chapter_service.get_chapter(db, project.id, chapter_id)
        return {
            "id": chapter.id,
            "project_id": chapter.project_id,
            "volume_id": chapter.volume_id,
            "title": chapter.title,
            "sequence": chapter.sequence,
            "status": chapter.status,
            "contract": chapter.contract,
            "scenes": [
                {
                    "id": s.id,
                    "chapter_id": s.chapter_id,
                    "title": s.title,
                    "sequence": s.sequence,
                    "pov": s.pov,
                    "location": s.location,
                    "status": s.status,
                    "current_revision_id": s.current_revision_id,
                    "content": get_scene_content(db, s),
                    "entry_contract": s.entry_contract,
                    "exit_state": s.exit_state,
                }
                for s in scenes
            ],
        }


@router.put("/api/chapters/{chapter_id}", response_model=ChapterView)
def update_chapter(chapter_id: int, payload: ChapterUpdate, state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        chapter = chapter_service.update_chapter(
            db,
            project_id=project.id,
            chapter_id=chapter_id,
            title=payload.title,
            volume_id=payload.volume_id,
            contract=payload.contract,
        )
        return {
            "id": chapter.id,
            "project_id": chapter.project_id,
            "volume_id": chapter.volume_id,
            "title": chapter.title,
            "sequence": chapter.sequence,
            "status": chapter.status,
            "contract": chapter.contract,
        }


@router.post("/api/chapters/{chapter_id}/status")
def update_chapter_status(chapter_id: int, payload: ChapterStatusUpdate, state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        chapter = chapter_service.change_chapter_status(db, project.id, chapter_id, payload.status)
        return {"id": chapter.id, "status": chapter.status}


@router.delete("/api/chapters/{chapter_id}")
def delete_chapter(chapter_id: int, state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        deleted_id = chapter_service.delete_chapter(db, project.id, chapter_id)
        return {"status": "ok", "deleted_chapter_id": deleted_id}
