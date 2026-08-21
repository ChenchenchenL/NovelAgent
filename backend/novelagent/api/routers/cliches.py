from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query

from ..dependencies import AppState, require_session
from ...application.services import cliche_service, project_service
from ..schemas.quality import ClicheCreate, ClicheScanRequest, ClicheUpdate, ClicheView

router = APIRouter(tags=["Cliche Blacklist"])


def _to_cliche_view(c: Any) -> ClicheView:
    return ClicheView(
        id=c.id,
        project_id=c.project_id,
        pattern=c.pattern,
        pattern_type=c.pattern_type,
        category=c.category,
        genre=c.genre,
        severity=c.severity,
        suggestion=c.suggestion,
        version=c.version,
        enabled=c.enabled,
        created_at=c.created_at.isoformat() if c.created_at else "",
    )


@router.get("/api/cliche-blacklist", response_model=list[ClicheView])
def list_cliches_endpoint(
    genre: str | None = None,
    category: str | None = None,
    enabled_only: bool = False,
    state: AppState = Depends(require_session),
) -> list[ClicheView]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        entries = cliche_service.list_cliche_entries(db, project.id, genre=genre, category=category, enabled_only=enabled_only)
        return [_to_cliche_view(e) for e in entries]


@router.post("/api/cliche-blacklist", response_model=ClicheView)
def create_cliche_endpoint(
    payload: ClicheCreate,
    state: AppState = Depends(require_session),
) -> ClicheView:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        entry = cliche_service.create_cliche_entry(
            db,
            project_id=project.id,
            pattern=payload.pattern,
            pattern_type=payload.pattern_type,
            category=payload.category,
            genre=payload.genre,
            severity=payload.severity,
            suggestion=payload.suggestion,
            enabled=payload.enabled,
        )
        return _to_cliche_view(entry)


@router.put("/api/cliche-blacklist/{cliche_id}", response_model=ClicheView)
def update_cliche_endpoint(
    cliche_id: int,
    payload: ClicheUpdate,
    state: AppState = Depends(require_session),
) -> ClicheView:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        try:
            entry = cliche_service.update_cliche_entry(
                db,
                cliche_id,
                project.id,
                pattern=payload.pattern,
                pattern_type=payload.pattern_type,
                category=payload.category,
                genre=payload.genre,
                severity=payload.severity,
                suggestion=payload.suggestion,
                enabled=payload.enabled,
            )
            return _to_cliche_view(entry)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/api/cliche-blacklist/{cliche_id}")
def delete_cliche_endpoint(
    cliche_id: int,
    state: AppState = Depends(require_session),
) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        try:
            cliche_service.delete_cliche_entry(db, cliche_id, project.id)
            return {"status": "DELETED", "id": cliche_id}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))


@router.post("/api/cliche-blacklist/scan")
def scan_cliches_endpoint(
    payload: ClicheScanRequest,
    state: AppState = Depends(require_session),
) -> list[dict[str, Any]]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        return cliche_service.scan_text_cliches(db, project.id, payload.text, genre=payload.genre)
