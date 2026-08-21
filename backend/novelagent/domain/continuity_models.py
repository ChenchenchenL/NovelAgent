from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from ..infrastructure.db import Base


def now() -> datetime:
    return datetime.now(timezone.utc)


class Character(Base):
    __tablename__ = "characters"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    aliases: Mapped[list] = mapped_column(JSON, default=list)
    background: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    core_traits: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class CharacterState(Base):
    __tablename__ = "character_states"
    id: Mapped[int] = mapped_column(primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"), index=True)
    scene_id: Mapped[int] = mapped_column(ForeignKey("scenes.id"), index=True)
    narrative_time: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    physical_state: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    goal: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    faction: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    emotion: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    arc_stage: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)


class RelationshipEvent(Base):
    __tablename__ = "relationship_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    subject_character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"), index=True)
    object_character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"), index=True)
    relationship_type: Mapped[str] = mapped_column(String(32))
    scene_id: Mapped[int] = mapped_column(ForeignKey("scenes.id"), index=True)
    narrative_time: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class RelationshipState(Base):
    __tablename__ = "relationship_states"
    __table_args__ = (
        UniqueConstraint("project_id", "subject_character_id", "object_character_id", name="uq_relationship_subject_object"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    subject_character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"), index=True)
    object_character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"), index=True)
    relationship_type: Mapped[str] = mapped_column(String(32))
    as_of_scene_id: Mapped[int] = mapped_column(ForeignKey("scenes.id"))
    as_of_narrative_time: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)


class NarrativeSecret(Base):
    __tablename__ = "narrative_secrets"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    secret_name: Mapped[str] = mapped_column(String(255))
    secret_content: Mapped[str] = mapped_column(Text)
    created_scene_id: Mapped[int] = mapped_column(ForeignKey("scenes.id"))
    created_narrative_time: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    known_by: Mapped[list] = mapped_column(JSON, default=list)


class InformationGap(Base):
    __tablename__ = "information_gaps"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"), index=True)
    fact_description: Mapped[str] = mapped_column(Text)
    knows: Mapped[bool] = mapped_column(Boolean, default=False)
    last_updated_scene_id: Mapped[int] = mapped_column(ForeignKey("scenes.id"))


class IdentityHypothesis(Base):
    __tablename__ = "identity_hypotheses"
    id: Mapped[int] = mapped_column(primary_key=True)
    shadow_entity_id: Mapped[int] = mapped_column(ForeignKey("shadow_entities.id"), index=True)
    canonical_character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"), index=True)
    evidence: Mapped[list] = mapped_column(JSON, default=list)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    earliest_reveal_scene_id: Mapped[Optional[int]] = mapped_column(ForeignKey("scenes.id"), nullable=True)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)


class IdentityRevealEvent(Base):
    __tablename__ = "identity_reveal_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    shadow_entity_id: Mapped[int] = mapped_column(ForeignKey("shadow_entities.id"), index=True)
    canonical_character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"), index=True)
    reveal_scene_id: Mapped[int] = mapped_column(ForeignKey("scenes.id"), index=True)
    evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reader_visibility: Mapped[str] = mapped_column(String(32), default="FULL")
    character_knowledge: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class LocationEntity(Base):
    __tablename__ = "locations"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    parent_location_id: Mapped[Optional[int]] = mapped_column(ForeignKey("locations.id"), nullable=True)
    coordinates: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class TravelProfile(Base):
    __tablename__ = "travel_profiles"
    __table_args__ = (
        UniqueConstraint("project_id", "from_location_id", "to_location_id", "travel_mode", name="uq_travel_profile"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    from_location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), index=True)
    to_location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), index=True)
    travel_mode: Mapped[str] = mapped_column(String(32))
    min_duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    distance_units: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    special_rules: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class MovementEvent(Base):
    __tablename__ = "movement_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    subject_type: Mapped[str] = mapped_column(String(16))  # CHARACTER, ITEM
    subject_id: Mapped[int] = mapped_column(Integer, index=True)
    from_location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"))
    to_location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"))
    travel_mode: Mapped[str] = mapped_column(String(32))
    departure_scene_id: Mapped[int] = mapped_column(ForeignKey("scenes.id"))
    arrival_scene_id: Mapped[int] = mapped_column(ForeignKey("scenes.id"))
    departure_time: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    arrival_time: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    actual_duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
