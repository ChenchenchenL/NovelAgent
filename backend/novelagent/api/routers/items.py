from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import AppState, require_session
from ...application.services import continuity_item_service, project_service
from ..schemas.continuity import (
    ItemCreate,
    ItemEventCreate,
    ItemEventView,
    ItemView,
)

router = APIRouter(tags=["Items & Conservation"])


@router.get("/api/items", response_model=list[ItemView])
def list_items_endpoint(state: AppState = Depends(require_session)) -> list[ItemView]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        items = continuity_item_service.list_items(db, project.id)
        return [
            ItemView(
                id=i.id,
                project_id=i.project_id,
                name=i.name,
                unique_item=i.unique_item,
                current_holder=i.current_holder,
                current_state=i.current_state,
                current_location=i.current_location,
                derived_from_id=i.derived_from_id,
            )
            for i in items
        ]


@router.post("/api/items", response_model=ItemView)
def create_item_endpoint(payload: ItemCreate, state: AppState = Depends(require_session)) -> ItemView:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        item = continuity_item_service.create_item(
            db,
            project.id,
            payload.name,
            payload.unique_item,
            payload.current_holder,
            payload.current_state,
            payload.current_location,
            payload.derived_from_id,
        )
        return ItemView(
            id=item.id,
            project_id=item.project_id,
            name=item.name,
            unique_item=item.unique_item,
            current_holder=item.current_holder,
            current_state=item.current_state,
            current_location=item.current_location,
            derived_from_id=item.derived_from_id,
        )


@router.get("/api/items/{item_id}", response_model=ItemView)
def get_item_endpoint(item_id: int, state: AppState = Depends(require_session)) -> ItemView:
    _, factory = state.require_project()
    with factory() as db:
        try:
            item = continuity_item_service.get_item(db, item_id)
            return ItemView(
                id=item.id,
                project_id=item.project_id,
                name=item.name,
                unique_item=item.unique_item,
                current_holder=item.current_holder,
                current_state=item.current_state,
                current_location=item.current_location,
                derived_from_id=item.derived_from_id,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))


@router.post("/api/items/{item_id}/events", response_model=ItemEventView)
def record_item_event_endpoint(
    item_id: int, payload: ItemEventCreate, state: AppState = Depends(require_session)
) -> ItemEventView:
    _, factory = state.require_project()
    with factory() as db:
        try:
            evt = continuity_item_service.record_item_event(db, item_id, payload.model_dump())
            return ItemEventView(
                id=evt.id,
                item_id=evt.item_id,
                event_type=evt.event_type,
                from_holder=evt.from_holder,
                to_holder=evt.to_holder,
                from_location=evt.from_location,
                to_location=evt.to_location,
                narrative_time=evt.narrative_time,
                evidence=evt.evidence,
                scene_id=evt.scene_id,
                confirmed=evt.confirmed,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))


@router.get("/api/items/{item_id}/history", response_model=list[ItemEventView])
def get_item_history_endpoint(item_id: int, state: AppState = Depends(require_session)) -> list[ItemEventView]:
    _, factory = state.require_project()
    with factory() as db:
        try:
            events = continuity_item_service.get_item_history(db, item_id)
            return [
                ItemEventView(
                    id=e.id,
                    item_id=e.item_id,
                    event_type=e.event_type,
                    from_holder=e.from_holder,
                    to_holder=e.to_holder,
                    from_location=e.from_location,
                    to_location=e.to_location,
                    narrative_time=e.narrative_time,
                    evidence=e.evidence,
                    scene_id=e.scene_id,
                    confirmed=e.confirmed,
                )
                for e in events
            ]
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
