from __future__ import annotations

from typing import Any, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...domain.models import ItemEntity, ItemEvent
from ...domain.rules import ItemTransition, validate_item_transition


def create_item(
    session: Session,
    project_id: int,
    name: str,
    unique_item: bool = False,
    current_holder: str | None = None,
    current_state: str = "CREATED",
    current_location: str | None = None,
    derived_from_id: int | None = None,
) -> ItemEntity:
    item = ItemEntity(
        project_id=project_id,
        name=name.strip(),
        unique_item=unique_item,
        current_holder=current_holder,
        current_state=current_state,
        current_location=current_location,
        derived_from_id=derived_from_id,
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def get_item(session: Session, item_id: int) -> ItemEntity:
    item = session.get(ItemEntity, item_id)
    if not item:
        raise KeyError(f"物品不存在: ID {item_id}")
    return item


def list_items(session: Session, project_id: int) -> list[ItemEntity]:
    stmt = select(ItemEntity).where(ItemEntity.project_id == project_id).order_by(ItemEntity.id.asc())
    return list(session.scalars(stmt).all())


def record_item_event(
    session: Session,
    item_id: int,
    event_payload: dict[str, Any],
) -> ItemEvent:
    item = get_item(session, item_id)
    event_type = event_payload.get("event_type", "TRANSFERRED")
    from_holder = event_payload.get("from_holder")
    to_holder = event_payload.get("to_holder")
    from_location = event_payload.get("from_location")
    to_location = event_payload.get("to_location")
    narrative_time = event_payload.get("narrative_time")
    evidence = event_payload.get("evidence")
    scene_id = event_payload.get("scene_id")
    confirmed = event_payload.get("confirmed", False)

    transition = ItemTransition(
        event_type=event_type,
        from_holder=from_holder,
        to_holder=to_holder,
        from_location=from_location,
        to_location=to_location,
        narrative_time=narrative_time,
    )

    new_state = validate_item_transition(
        current_state=item.current_state,
        current_holder=item.current_holder,
        transition=transition,
        unique_item=item.unique_item,
    )

    item.current_state = new_state
    if event_type == "TRANSFERRED":
        item.current_holder = to_holder
    elif event_type == "LOST":
        item.current_holder = None
    elif event_type == "FOUND":
        item.current_holder = to_holder
    if to_location:
        item.current_location = to_location

    evt = ItemEvent(
        item_id=item.id,
        event_type=event_type,
        from_holder=from_holder,
        to_holder=to_holder,
        from_location=from_location,
        to_location=to_location,
        narrative_time=narrative_time,
        evidence=evidence,
        scene_id=scene_id,
        confirmed=confirmed,
    )
    session.add(evt)
    session.commit()
    session.refresh(evt)
    return evt


def get_item_history(session: Session, item_id: int) -> list[ItemEvent]:
    get_item(session, item_id)
    stmt = select(ItemEvent).where(ItemEvent.item_id == item_id).order_by(ItemEvent.id.asc())
    return list(session.scalars(stmt).all())
