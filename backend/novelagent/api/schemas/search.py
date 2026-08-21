from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


class FTSSearchRequest(BaseModel):
    query: str
    doc_type: Optional[str] = None
    modality: Optional[str] = None
    confirmed_only: bool = False
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class FTSSearchResultItem(BaseModel):
    id: int
    project_id: int
    doc_type: str
    source_id: int
    source_version: int
    content: str
    narrative_time: Optional[str] = None
    modality: str
    confirmed: bool
    score: float = 1.0


class VectorSearchRequest(BaseModel):
    query_text: str
    doc_type: Optional[str] = None
    top_k: int = Field(default=10, ge=1, le=100)
    min_similarity: float = Field(default=0.0, ge=0.0, le=1.0)


class VectorSearchResultItem(BaseModel):
    id: int
    project_id: int
    doc_type: str
    source_id: int
    source_version: int
    content: str
    narrative_time: Optional[str] = None
    modality: str
    confirmed: bool
    similarity: float


class KGNodeView(BaseModel):
    id: int
    project_id: int
    node_type: str
    entity_id: int
    name: str
    narrative_time: Optional[str] = None
    modality: str
    confirmed: bool


class KGEdgeView(BaseModel):
    id: int
    project_id: int
    source_node_id: int
    target_node_id: int
    edge_type: str
    narrative_time: Optional[str] = None
    modality: str
    confirmed: bool
    source_scene_id: Optional[int] = None
    weight: float = 1.0


class KGPathQueryRequest(BaseModel):
    source_node_id: int
    target_node_id: int
    max_hops: int = Field(default=3, ge=1, le=10)
    edge_types: Optional[list[str]] = None


class SummaryView(BaseModel):
    id: int
    project_id: int
    summary_type: str
    source_id: int
    source_version: int
    content: str
    covered_node_ids: list[int] = Field(default_factory=list)
    narrative_time_range: Optional[str] = None


class SummaryCreateRequest(BaseModel):
    summary_type: str
    source_id: int
    source_version: int = 1
    content: str
    covered_node_ids: Optional[list[int]] = None
    narrative_time_range: Optional[str] = None


class HRAGRetrieveRequest(BaseModel):
    scene_id: int
    max_tokens: int = Field(default=4000, ge=100, le=32000)
    include_plot_threads: bool = True
    include_adjacent_scenes: bool = True
    include_recent_text: bool = True


class ContextPackAssembleRequest(BaseModel):
    scene_id: int
    instruction: Optional[str] = None
    selection: Optional[str] = None
    max_tokens: int = Field(default=8000, ge=100, le=64000)
    include_kg_paths: bool = False
    include_community_summaries: bool = False


class ContextPackValidateRequest(BaseModel):
    pack_data: dict[str, Any]


class IndexRebuildResponse(BaseModel):
    status: str
    project_id: int
    fts_documents: int
    vector_documents: int
    kg_nodes: int
    kg_edges: int
    summaries: int


class IndexStatusView(BaseModel):
    project_id: int
    overall_status: str
    fts: dict[str, Any]
    vector: dict[str, Any]
    kg: dict[str, Any]
    summaries: dict[str, Any]
    details: dict[str, Any]
