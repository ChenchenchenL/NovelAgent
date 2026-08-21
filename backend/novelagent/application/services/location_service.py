from __future__ import annotations

from typing import Any, Optional
from sqlalchemy import delete, or_, select, update
from sqlalchemy.orm import Session

from ...domain.continuity_models import Character, LocationEntity, MovementEvent, TravelProfile
from ...domain.models import ItemEntity, Scene, ShadowEntity
from ...domain.rules import calculate_time_delta_minutes, evaluate_movement_feasibility


def create_location(
    session: Session,
    project_id: int,
    name: str,
    parent_location_id: int | None = None,
    coordinates: dict[str, Any] | None = None,
    description: str | None = None,
) -> LocationEntity:
    loc = LocationEntity(
        project_id=project_id,
        name=name.strip(),
        parent_location_id=parent_location_id,
        coordinates=coordinates,
        description=description,
    )
    session.add(loc)
    session.commit()
    session.refresh(loc)
    return loc


def get_location(session: Session, location_id: int) -> LocationEntity:
    loc = session.get(LocationEntity, location_id)
    if not loc:
        raise KeyError(f"地点不存在: ID {location_id}")
    return loc


def list_locations(session: Session, project_id: int) -> list[LocationEntity]:
    stmt = select(LocationEntity).where(LocationEntity.project_id == project_id).order_by(LocationEntity.id.asc())
    return list(session.scalars(stmt).all())


def update_location(
    session: Session,
    location_id: int,
    name: str | None = None,
    parent_location_id: int | None = None,
    coordinates: dict[str, Any] | None = None,
    description: str | None = None,
) -> LocationEntity:
    loc = get_location(session, location_id)
    if name is not None:
        loc.name = name.strip()
    if parent_location_id is not None:
        loc.parent_location_id = parent_location_id
    if coordinates is not None:
        loc.coordinates = coordinates
    if description is not None:
        loc.description = description
    session.commit()
    session.refresh(loc)
    return loc


def delete_location(session: Session, location_id: int) -> None:
    loc = get_location(session, location_id)
    # Cascade cleanup profiles, movement events, and unlink child locations
    session.execute(
        delete(TravelProfile).where(
            or_(
                TravelProfile.from_location_id == location_id,
                TravelProfile.to_location_id == location_id,
            )
        )
    )
    session.execute(
        delete(MovementEvent).where(
            or_(
                MovementEvent.from_location_id == location_id,
                MovementEvent.to_location_id == location_id,
            )
        )
    )
    session.execute(
        update(LocationEntity)
        .where(LocationEntity.parent_location_id == location_id)
        .values(parent_location_id=None)
    )
    session.delete(loc)
    session.commit()


def create_travel_profile(
    session: Session,
    project_id: int,
    from_location_id: int,
    to_location_id: int,
    travel_mode: str,
    min_duration_minutes: int | None = None,
    distance_units: float | None = None,
    special_rules: str | None = None,
) -> TravelProfile:
    get_location(session, from_location_id)
    get_location(session, to_location_id)

    profile = session.scalar(
        select(TravelProfile).where(
            TravelProfile.project_id == project_id,
            TravelProfile.from_location_id == from_location_id,
            TravelProfile.to_location_id == to_location_id,
            TravelProfile.travel_mode == travel_mode,
        )
    )
    if not profile:
        profile = TravelProfile(
            project_id=project_id,
            from_location_id=from_location_id,
            to_location_id=to_location_id,
            travel_mode=travel_mode,
            min_duration_minutes=min_duration_minutes,
            distance_units=distance_units,
            special_rules=special_rules,
        )
        session.add(profile)
    else:
        profile.min_duration_minutes = min_duration_minutes
        profile.distance_units = distance_units
        profile.special_rules = special_rules

    session.commit()
    session.refresh(profile)
    return profile


def list_travel_profiles(session: Session, project_id: int) -> list[TravelProfile]:
    stmt = select(TravelProfile).where(TravelProfile.project_id == project_id).order_by(TravelProfile.id.asc())
    return list(session.scalars(stmt).all())


def delete_travel_profile(session: Session, profile_id: int) -> None:
    p = session.get(TravelProfile, profile_id)
    if p:
        session.delete(p)
        session.commit()


def record_movement_event(
    session: Session,
    project_id: int,
    payload: dict[str, Any],
) -> tuple[MovementEvent, dict[str, Any]]:
    subject_type = payload.get("subject_type", "CHARACTER")
    subject_id = payload["subject_id"]

    # Polymorphic subject validation
    if subject_type == "CHARACTER":
        if not session.get(Character, subject_id):
            raise KeyError(f"移动主体人物不存在: ID {subject_id}")
    elif subject_type == "ITEM":
        if not session.get(ItemEntity, subject_id):
            raise KeyError(f"移动主体物品不存在: ID {subject_id}")
    elif subject_type == "SHADOW":
        if not session.get(ShadowEntity, subject_id):
            raise KeyError(f"移动主体影子实体不存在: ID {subject_id}")
    else:
        raise ValueError(f"未知移动主体类型: {subject_type}")

    from_id = payload["from_location_id"]
    to_id = payload["to_location_id"]
    travel_mode = payload.get("travel_mode", "WALK")
    dep_time = payload.get("departure_time")
    arr_time = payload.get("arrival_time")
    actual_duration = payload.get("actual_duration_minutes")

    if actual_duration is None:
        actual_duration = calculate_time_delta_minutes(dep_time, arr_time)

    profile = session.scalar(
        select(TravelProfile).where(
            TravelProfile.project_id == project_id,
            TravelProfile.from_location_id == from_id,
            TravelProfile.to_location_id == to_id,
            TravelProfile.travel_mode == travel_mode,
        )
    )
    min_dur = profile.min_duration_minutes if profile else None

    feasibility = evaluate_movement_feasibility(
        from_location_id=from_id,
        to_location_id=to_id,
        travel_mode=travel_mode,
        min_duration_minutes=min_dur,
        actual_duration_minutes=actual_duration,
    )

    evt = MovementEvent(
        project_id=project_id,
        subject_type=subject_type,
        subject_id=subject_id,
        from_location_id=from_id,
        to_location_id=to_id,
        travel_mode=travel_mode,
        departure_scene_id=payload["departure_scene_id"],
        arrival_scene_id=payload["arrival_scene_id"],
        departure_time=dep_time,
        arrival_time=arr_time,
        actual_duration_minutes=actual_duration,
        confirmed=payload.get("confirmed", False),
    )
    session.add(evt)
    session.commit()
    session.refresh(evt)
    return evt, feasibility


def check_scene_movement(
    session: Session,
    project_id: int,
    scene_id: int,
    from_id: int,
    to_id: int,
    travel_mode: str,
    departure_time: str | None = None,
    arrival_time: str | None = None,
    actual_duration: int | None = None,
) -> dict[str, Any]:
    scene = session.get(Scene, scene_id)
    if not scene:
        raise KeyError(f"场景不存在: ID {scene_id}")

    profile = session.scalar(
        select(TravelProfile).where(
            TravelProfile.project_id == project_id,
            TravelProfile.from_location_id == from_id,
            TravelProfile.to_location_id == to_id,
            TravelProfile.travel_mode == travel_mode,
        )
    )
    min_dur = profile.min_duration_minutes if profile else None
    dur = actual_duration or calculate_time_delta_minutes(departure_time, arrival_time)
    res = evaluate_movement_feasibility(from_id, to_id, travel_mode, min_dur, dur)
    res["scene_id"] = scene_id
    return res
