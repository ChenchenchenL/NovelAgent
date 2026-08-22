from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


# 1. Community Schemas
class CommunityCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    community_type: str = Field("CUSTOM", description="VOLUME, PLOT_THREAD, FACTION, CUSTOM")
    source_entity_type: Optional[str] = None
    source_entity_id: Optional[int] = None
    tags: list[str] = Field(default_factory=list)


class CommunityUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    tags: Optional[list[str]] = None
    status: Optional[str] = None


class CommunityResponse(BaseModel):
    id: int
    project_id: int
    name: str
    community_type: str
    source_entity_type: Optional[str] = None
    source_entity_id: Optional[int] = None
    tags: list[str] = Field(default_factory=list)
    status: str
    version: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CommunitySummaryResponse(BaseModel):
    id: int
    community_id: int
    project_id: int
    summary_type: str
    content: str
    covered_node_ids: list[int] = Field(default_factory=list)
    covered_edge_ids: list[int] = Field(default_factory=list)
    source_versions: dict[str, Any] = Field(default_factory=dict)
    algorithm_version: str
    token_count: int
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# 2. GraphRAG Query Schemas
class GraphRAGQueryCreate(BaseModel):
    query_type: str = Field("MULTI_HOP", description="CROSS_VOLUME, MULTI_HOP, GLOBAL_THEME, FORESHADOW_NETWORK, CHARACTER_ARC")
    query_text: str = Field(..., min_length=1)
    parameters: dict[str, Any] = Field(default_factory=dict)


class GraphRAGQueryResponse(BaseModel):
    id: int
    project_id: int
    query_type: str
    query_text: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    result: Optional[dict[str, Any]] = None
    communities_used: list[int] = Field(default_factory=list)
    token_cost: int
    duration_ms: int
    status: str
    created_at: Optional[datetime] = None


# 3. Global Analysis Report Schemas
class GlobalAnalysisReportResponse(BaseModel):
    id: int
    project_id: int
    report_type: str
    content: dict[str, Any] = Field(default_factory=dict)
    summary: str
    affected_entities: list[int] = Field(default_factory=list)
    severity_counts: dict[str, Any] = Field(default_factory=dict)
    token_cost: int
    duration_ms: int
    status: str
    created_at: Optional[datetime] = None


# 4. Model Stats Schemas
class ModelStatsDailyResponse(BaseModel):
    id: int
    project_id: int
    date: date
    model_name: str
    tier: str
    task_type: str
    total_calls: int
    success_calls: int
    failed_calls: int
    degraded_calls: int
    total_prompt_tokens: int
    total_completion_tokens: int
    total_tokens: int
    avg_duration_ms: int
    p90_duration_ms: int
    estimated_cost: float


class ModelStatsSummaryResponse(BaseModel):
    project_id: int
    total_calls: int
    success_calls: int
    failed_calls: int
    degraded_calls: int
    degradation_rate: float
    total_tokens: int
    estimated_cost_usd: float
    records_count: int


# 5. Feedback Optimization Schemas
class FeedbackOptimizationApplyRequest(BaseModel):
    issue_type: str
    action: str = "SUPPRESS"
    reason: Optional[str] = None
