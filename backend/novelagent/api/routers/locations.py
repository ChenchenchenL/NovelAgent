from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from ..dependencies import AppState, require_session
from ...application.services import location_service, project_service
from ...domain.continuity_models import MovementEvent
from ..schemas.continuity import (
    LocationCreate,
    LocationUpdate,
    LocationView,
    MovementCheckRequest,
    MovementEventCreate,
    MovementEventView,
    TravelProfileCreate,
    TravelProfileView,
)

router = APIRouter(tags=["Locations & Space Continuity"])


@router.get("/api/locations", response_model=list[LocationView])
def list_locations_endpoint(state: AppState = Depends(require_session)) -> list[LocationView]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        locs = location_service.list_locations(db, project.id)
        return [
            LocationView(
                id=l.id,
                project_id=l.project_id,
                name=l.name,
                parent_location_id=l.parent_location_id,
                coordinates=l.coordinates,
                description=l.description,
            )
            for l in locs
        ]


@router.post("/api/locations", response_model=LocationView)
def create_location_endpoint(payload: LocationCreate, state: AppState = Depends(require_session)) -> LocationView:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        l = location_service.create_location(
            db,
            project.id,
            payload.name,
            payload.parent_location_id,
            payload.coordinates,
            payload.description,
        )
        return LocationView(
            id=l.id,
            project_id=l.project_id,
            name=l.name,
            parent_location_id=l.parent_location_id,
            coordinates=l.coordinates,
            description=l.description,
        )


@router.get("/api/locations/{location_id}", response_model=LocationView)
def get_location_endpoint(location_id: int, state: AppState = Depends(require_session)) -> LocationView:
    _, factory = state.require_project()
    with factory() as db:
        try:
            l = location_service.get_location(db, location_id)
            return LocationView(
                id=l.id,
                project_id=l.project_id,
                name=l.name,
                parent_location_id=l.parent_location_id,
                coordinates=l.coordinates,
                description=l.description,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))


@router.put("/api/locations/{location_id}", response_model=LocationView)
def update_location_endpoint(
    location_id: int, payload: LocationUpdate, state: AppState = Depends(require_session)
) -> LocationView:
    _, factory = state.require_project()
    with factory() as db:
        try:
            l = location_service.update_location(
                db,
                location_id,
                payload.name,
                payload.parent_location_id,
                payload.coordinates,
                payload.description,
            )
            return LocationView(
                id=l.id,
                project_id=l.project_id,
                name=l.name,
                parent_location_id=l.parent_location_id,
                coordinates=l.coordinates,
                description=l.description,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/api/locations/{location_id}")
def delete_location_endpoint(location_id: int, state: AppState = Depends(require_session)) -> dict[str, bool]:
    _, factory = state.require_project()
    with factory() as db:
        try:
            location_service.delete_location(db, location_id)
            return {"ok": True}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))


@router.get("/api/travel-profiles", response_model=list[TravelProfileView])
def list_travel_profiles_endpoint(state: AppState = Depends(require_session)) -> list[TravelProfileView]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        profiles = location_service.list_travel_profiles(db, project.id)
        return [
            TravelProfileView(
                id=p.id,
                project_id=p.project_id,
                from_location_id=p.from_location_id,
                to_location_id=p.to_location_id,
                travel_mode=p.travel_mode,
                min_duration_minutes=p.min_duration_minutes,
                distance_units=p.distance_units,
                special_rules=p.special_rules,
            )
            for p in profiles
        ]


@router.post("/api/travel-profiles", response_model=TravelProfileView)
def create_travel_profile_endpoint(
    payload: TravelProfileCreate, state: AppState = Depends(require_session)
) -> TravelProfileView:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        try:
            p = location_service.create_travel_profile(
                db,
                project.id,
                payload.from_location_id,
                payload.to_location_id,
                payload.travel_mode,
                payload.min_duration_minutes,
                payload.distance_units,
                payload.special_rules,
            )
            return TravelProfileView(
                id=p.id,
                project_id=p.project_id,
                from_location_id=p.from_location_id,
                to_location_id=p.to_location_id,
                travel_mode=p.travel_mode,
                min_duration_minutes=p.min_duration_minutes,
                distance_units=p.distance_units,
                special_rules=p.special_rules,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/api/travel-profiles/{profile_id}")
def delete_travel_profile_endpoint(profile_id: int, state: AppState = Depends(require_session)) -> dict[str, bool]:
    _, factory = state.require_project()
    with factory() as db:
        location_service.delete_travel_profile(db, profile_id)
        return {"ok": True}


@router.get("/api/movements", response_model=list[MovementEventView])
def list_movements_endpoint(state: AppState = Depends(require_session)) -> list[MovementEventView]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        events = db.scalars(
            select(MovementEvent).where(MovementEvent.project_id == project.id).order_by(MovementEvent.id.asc())
        ).all()
        return [
            MovementEventView(
                id=e.id,
                project_id=e.project_id,
                subject_type=e.subject_type,
                subject_id=e.subject_id,
                from_location_id=e.from_location_id,
                to_location_id=e.to_location_id,
                travel_mode=e.travel_mode,
                departure_scene_id=e.departure_scene_id,
                arrival_scene_id=e.arrival_scene_id,
                departure_time=e.departure_time,
                arrival_time=e.arrival_time,
                actual_duration_minutes=e.actual_duration_minutes,
                confirmed=e.confirmed,
            )
            for e in events
        ]


@router.post("/api/movements")
def create_movement_endpoint(payload: MovementEventCreate, state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        try:
            evt, feasibility = location_service.record_movement_event(db, project.id, payload.model_dump())
            return {
                "event": MovementEventView(
                    id=evt.id,
                    project_id=evt.project_id,
                    subject_type=evt.subject_type,
                    subject_id=evt.subject_id,
                    from_location_id=evt.from_location_id,
                    to_location_id=evt.to_location_id,
                    travel_mode=evt.travel_mode,
                    departure_scene_id=evt.departure_scene_id,
                    arrival_scene_id=evt.arrival_scene_id,
                    departure_time=evt.departure_time,
                    arrival_time=evt.arrival_time,
                    actual_duration_minutes=evt.actual_duration_minutes,
                    confirmed=evt.confirmed,
                ),
                "feasibility": feasibility,
            }
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/scenes/{scene_id}/check-movement")
def check_scene_movement_endpoint(
    scene_id: int, payload: MovementCheckRequest, state: AppState = Depends(require_session)
) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        try:
            return location_service.check_scene_movement(
                db,
                project.id,
                scene_id,
                payload.from_location_id,
                payload.to_location_id,
                payload.travel_mode,
                payload.departure_time,
                payload.arrival_time,
                payload.actual_duration_minutes,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
