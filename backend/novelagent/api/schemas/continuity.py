from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


# 1. Characters & States
class CharacterCreate(BaseModel):
    name: str
    aliases: list[str] = Field(default_factory=list)
    background: Optional[str] = None
    core_traits: list[str] = Field(default_factory=list)


class CharacterUpdate(BaseModel):
    name: Optional[str] = None
    aliases: Optional[list[str]] = None
    background: Optional[str] = None
    core_traits: Optional[list[str]] = None


class CharacterView(BaseModel):
    id: int
    project_id: int
    name: str
    aliases: list[str] = Field(default_factory=list)
    background: Optional[str] = None
    core_traits: list[str] = Field(default_factory=list)
    created_at: Optional[str] = None


class CharacterStateCreate(BaseModel):
    scene_id: int
    narrative_time: Optional[str] = None
    location: Optional[str] = None
    physical_state: Optional[str] = None
    goal: Optional[str] = None
    faction: Optional[str] = None
    emotion: Optional[str] = None
    arc_stage: Optional[str] = None
    confirmed: bool = False


class CharacterStateView(BaseModel):
    id: int
    character_id: int
    scene_id: int
    narrative_time: Optional[str] = None
    location: Optional[str] = None
    physical_state: Optional[str] = None
    goal: Optional[str] = None
    faction: Optional[str] = None
    emotion: Optional[str] = None
    arc_stage: Optional[str] = None
    confirmed: bool = False


# 2. Relationships
class RelationshipEventCreate(BaseModel):
    subject_character_id: int
    object_character_id: int
    relationship_type: str
    scene_id: int
    narrative_time: Optional[str] = None
    evidence: Optional[str] = None
    confirmed: bool = False


class RelationshipEventView(BaseModel):
    id: int
    project_id: int
    subject_character_id: int
    object_character_id: int
    relationship_type: str
    scene_id: int
    narrative_time: Optional[str] = None
    evidence: Optional[str] = None
    confirmed: bool = False
    created_at: Optional[str] = None


class RelationshipStateView(BaseModel):
    id: int
    project_id: int
    subject_character_id: int
    object_character_id: int
    relationship_type: str
    as_of_scene_id: int
    as_of_narrative_time: Optional[str] = None
    updated_at: Optional[str] = None


# 3. Secrets & Knowledge
class SecretCreate(BaseModel):
    secret_name: str
    secret_content: str
    created_scene_id: int
    created_narrative_time: Optional[str] = None
    known_by: list[dict[str, Any]] = Field(default_factory=list)


class SecretView(BaseModel):
    id: int
    project_id: int
    secret_name: str
    secret_content: str
    created_scene_id: int
    created_narrative_time: Optional[str] = None
    known_by: list[dict[str, Any]] = Field(default_factory=list)


class SecretRevealRequest(BaseModel):
    character_id: int
    scene_id: int
    narrative_time: Optional[str] = None


class KnowledgeCheckRequest(BaseModel):
    character_id: int
    secret_ids: list[int] = Field(default_factory=list)


# 4. Items
class ItemCreate(BaseModel):
    name: str
    unique_item: bool = False
    current_holder: Optional[str] = None
    current_state: str = "CREATED"
    current_location: Optional[str] = None
    derived_from_id: Optional[int] = None


class ItemView(BaseModel):
    id: int
    project_id: int
    name: str
    unique_item: bool = False
    current_holder: Optional[str] = None
    current_state: str = "CREATED"
    current_location: Optional[str] = None
    derived_from_id: Optional[int] = None


class ItemEventCreate(BaseModel):
    event_type: str
    from_holder: Optional[str] = None
    to_holder: Optional[str] = None
    from_location: Optional[str] = None
    to_location: Optional[str] = None
    narrative_time: Optional[str] = None
    evidence: Optional[str] = None
    scene_id: Optional[int] = None
    confirmed: bool = False


class ItemEventView(BaseModel):
    id: int
    item_id: int
    event_type: str
    from_holder: Optional[str] = None
    to_holder: Optional[str] = None
    from_location: Optional[str] = None
    to_location: Optional[str] = None
    narrative_time: Optional[str] = None
    evidence: Optional[str] = None
    scene_id: Optional[int] = None
    confirmed: bool = False


# 5. Shadows & Hypotheses
class ShadowEntityCreate(BaseModel):
    display_name: str


class ShadowEntityView(BaseModel):
    id: int
    project_id: int
    display_name: str
    canonical_character: Optional[str] = None
    canonical_character_id: Optional[int] = None
    revealed_scene_id: Optional[int] = None
    revealed: bool = False


class IdentityHypothesisCreate(BaseModel):
    canonical_character_id: int
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    confidence: float = 0.0
    earliest_reveal_scene_id: Optional[int] = None
    confirmed: bool = False


class IdentityHypothesisView(BaseModel):
    id: int
    shadow_entity_id: int
    canonical_character_id: int
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    confidence: float = 0.0
    earliest_reveal_scene_id: Optional[int] = None
    confirmed: bool = False


class IdentityRevealRequest(BaseModel):
    canonical_character_id: int
    reveal_scene_id: int
    evidence: Optional[str] = None
    reader_visibility: str = "FULL"
    character_knowledge: list[dict[str, Any]] = Field(default_factory=list)


class IdentityRevealView(BaseModel):
    id: int
    shadow_entity_id: int
    canonical_character_id: int
    reveal_scene_id: int
    evidence: Optional[str] = None
    reader_visibility: str = "FULL"
    character_knowledge: list[dict[str, Any]] = Field(default_factory=list)
    created_at: Optional[str] = None


# 6. Locations & Movements
class LocationCreate(BaseModel):
    name: str
    parent_location_id: Optional[int] = None
    coordinates: Optional[dict[str, Any]] = None
    description: Optional[str] = None


class LocationUpdate(BaseModel):
    name: Optional[str] = None
    parent_location_id: Optional[int] = None
    coordinates: Optional[dict[str, Any]] = None
    description: Optional[str] = None


class LocationView(BaseModel):
    id: int
    project_id: int
    name: str
    parent_location_id: Optional[int] = None
    coordinates: Optional[dict[str, Any]] = None
    description: Optional[str] = None


class TravelProfileCreate(BaseModel):
    from_location_id: int
    to_location_id: int
    travel_mode: str
    min_duration_minutes: Optional[int] = None
    distance_units: Optional[float] = None
    special_rules: Optional[str] = None


class TravelProfileView(BaseModel):
    id: int
    project_id: int
    from_location_id: int
    to_location_id: int
    travel_mode: str
    min_duration_minutes: Optional[int] = None
    distance_units: Optional[float] = None
    special_rules: Optional[str] = None


class MovementEventCreate(BaseModel):
    subject_type: str = "CHARACTER"
    subject_id: int
    from_location_id: int
    to_location_id: int
    travel_mode: str = "WALK"
    departure_scene_id: int
    arrival_scene_id: int
    departure_time: Optional[str] = None
    arrival_time: Optional[str] = None
    actual_duration_minutes: Optional[int] = None
    confirmed: bool = False


class MovementEventView(BaseModel):
    id: int
    project_id: int
    subject_type: str
    subject_id: int
    from_location_id: int
    to_location_id: int
    travel_mode: str
    departure_scene_id: int
    arrival_scene_id: int
    departure_time: Optional[str] = None
    arrival_time: Optional[str] = None
    actual_duration_minutes: Optional[int] = None
    confirmed: bool = False


class MovementCheckRequest(BaseModel):
    from_location_id: int
    to_location_id: int
    travel_mode: str = "WALK"
    departure_time: Optional[str] = None
    arrival_time: Optional[str] = None
    actual_duration_minutes: Optional[int] = None
