from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


# 1. Plot Threads
class PlotThreadCreate(BaseModel):
    name: str
    thread_type: str = "MAIN"
    priority: int = 1
    description: Optional[str] = None
    start_scene_id: Optional[int] = None


class PlotThreadUpdate(BaseModel):
    name: Optional[str] = None
    thread_type: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[int] = None
    description: Optional[str] = None
    start_scene_id: Optional[int] = None
    end_scene_id: Optional[int] = None


class PlotThreadView(BaseModel):
    id: int
    project_id: int
    name: str
    thread_type: str = "MAIN"
    status: str = "ACTIVE"
    priority: int = 1
    description: Optional[str] = None
    start_scene_id: Optional[int] = None
    end_scene_id: Optional[int] = None
    created_at: Optional[str] = None


# 2. Plot Events
class PlotEventCreate(BaseModel):
    plot_thread_id: int
    event_type: str
    scene_id: int
    narrative_time: Optional[str] = None
    description: str
    evidence: Optional[str] = None
    confirmed: bool = False


class PlotEventView(BaseModel):
    id: int
    plot_thread_id: int
    event_type: str
    scene_id: int
    narrative_time: Optional[str] = None
    description: str
    evidence: Optional[str] = None
    confirmed: bool = False
    created_at: Optional[str] = None


# 3. Foreshadowings
class ForeshadowingCreate(BaseModel):
    name: str
    setup_scene_id: int
    plot_thread_id: Optional[int] = None
    priority: str = "SUBPLOT"
    target_chapter_start: Optional[int] = None
    target_chapter_end: Optional[int] = None
    earliest_trigger_chapter: Optional[int] = None
    latest_payoff_chapter: Optional[int] = None
    trigger_condition_type: Optional[str] = None
    trigger_condition_params: Optional[dict[str, Any]] = None
    visibility: str = "AUTHOR"
    visible_to_character_id: Optional[int] = None
    anchors: list[dict[str, Any]] = Field(default_factory=list)
    description: Optional[str] = None
    confirmed: bool = False


class ForeshadowingUpdate(BaseModel):
    name: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    target_chapter_start: Optional[int] = None
    target_chapter_end: Optional[int] = None
    earliest_trigger_chapter: Optional[int] = None
    latest_payoff_chapter: Optional[int] = None
    trigger_condition_type: Optional[str] = None
    trigger_condition_params: Optional[dict[str, Any]] = None
    visibility: Optional[str] = None
    visible_to_character_id: Optional[int] = None
    anchors: Optional[list[dict[str, Any]]] = None
    description: Optional[str] = None


class ForeshadowingPayoffRequest(BaseModel):
    payoff_scene_id: int
    description: Optional[str] = None


class ForeshadowingView(BaseModel):
    id: int
    project_id: int
    plot_thread_id: Optional[int] = None
    name: str
    status: str = "SETUP"
    priority: str = "SUBPLOT"
    target_chapter_start: Optional[int] = None
    target_chapter_end: Optional[int] = None
    earliest_trigger_chapter: Optional[int] = None
    latest_payoff_chapter: Optional[int] = None
    trigger_condition_type: Optional[str] = None
    trigger_condition_params: Optional[dict[str, Any]] = None
    visibility: str = "AUTHOR"
    visible_to_character_id: Optional[int] = None
    anchors: list[dict[str, Any]] = Field(default_factory=list)
    setup_scene_id: int
    payoff_scene_id: Optional[int] = None
    description: Optional[str] = None
    confirmed: bool = False
    created_at: Optional[str] = None


# 4. Transitions
class TransitionCheckRequest(BaseModel):
    prev_scene_id: Optional[int] = None
    entry_contract_override: Optional[dict[str, Any]] = None


class SceneContractsUpdateRequest(BaseModel):
    entry_contract: Optional[dict[str, Any]] = None
    exit_state: Optional[dict[str, Any]] = None


# 5. Impact Graph
class ImpactNodeCreate(BaseModel):
    node_type: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    scene_id: Optional[int] = None
    revision_id: Optional[int] = None
    narrative_time: Optional[str] = None
    content_hash: Optional[str] = None


class ImpactNodeView(BaseModel):
    id: int
    project_id: int
    node_type: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    scene_id: Optional[int] = None
    revision_id: Optional[int] = None
    narrative_time: Optional[str] = None
    content_hash: Optional[str] = None
    created_at: Optional[str] = None


class ImpactEdgeCreate(BaseModel):
    source_node_id: int
    target_node_id: int
    edge_type: str
    weight: float = 1.0


class ImpactEdgeView(BaseModel):
    id: int
    project_id: int
    source_node_id: int
    target_node_id: int
    edge_type: str
    weight: float = 1.0
    created_at: Optional[str] = None


class ImpactPropagateRequest(BaseModel):
    changed_node_id: int
    change_type: str = "MODIFIED"
