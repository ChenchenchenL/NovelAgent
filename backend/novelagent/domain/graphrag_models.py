from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Optional

from sqlalchemy import (
    JSON,
    Date,
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


class Community(Base):
    __tablename__ = "communities"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    community_type: Mapped[str] = mapped_column(String(32), index=True)
    # VOLUME, PLOT_THREAD, FACTION, CUSTOM
    source_entity_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    source_entity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE")
    # ACTIVE, STALE, REBUILDING
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)


class CommunitySummary(Base):
    __tablename__ = "community_summaries"

    id: Mapped[int] = mapped_column(primary_key=True)
    community_id: Mapped[int] = mapped_column(ForeignKey("communities.id"), index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    summary_type: Mapped[str] = mapped_column(String(32))
    # OVERVIEW, CHARACTER_RELATIONS, PLOT_PROGRESS, ITEM_FLOWS, SECRET_SPREAD
    content: Mapped[str] = mapped_column(Text)
    covered_node_ids: Mapped[list] = mapped_column(JSON, default=list)
    covered_edge_ids: Mapped[list] = mapped_column(JSON, default=list)
    source_versions: Mapped[dict] = mapped_column(JSON, default=dict)
    algorithm_version: Mapped[str] = mapped_column(String(32), default="v1")
    token_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(32), default="VALID")
    # VALID, STALE, REBUILDING, FAILED
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)


class GraphRAGQuery(Base):
    __tablename__ = "graphrag_queries"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    query_type: Mapped[str] = mapped_column(String(32))
    # CROSS_VOLUME, MULTI_HOP, GLOBAL_THEME, FORESHADOW_NETWORK, CHARACTER_ARC
    query_text: Mapped[str] = mapped_column(Text)
    parameters: Mapped[dict] = mapped_column(JSON, default=dict)
    result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    communities_used: Mapped[list] = mapped_column(JSON, default=list)
    token_cost: Mapped[int] = mapped_column(Integer, default=0)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(32), default="PENDING")
    # PENDING, RUNNING, COMPLETED, FAILED
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class GlobalAnalysisReport(Base):
    __tablename__ = "global_analysis_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    report_type: Mapped[str] = mapped_column(String(32), index=True)
    # CHARACTER_ARC, RELATIONSHIP_NETWORK, FORESHADOW_AUDIT,
    # SPATIAL_TEMPORAL, STYLE_DRIFT, PLOT_RUPTURE
    content: Mapped[dict] = mapped_column(JSON, default=dict)
    summary: Mapped[str] = mapped_column(Text)
    affected_entities: Mapped[list] = mapped_column(JSON, default=list)
    severity_counts: Mapped[dict] = mapped_column(JSON, default=dict)
    token_cost: Mapped[int] = mapped_column(Integer, default=0)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(32), default="COMPLETED")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class ModelStatsDaily(Base):
    __tablename__ = "model_stats_daily"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    model_name: Mapped[str] = mapped_column(String(255))
    tier: Mapped[str] = mapped_column(String(8))
    task_type: Mapped[str] = mapped_column(String(64))
    total_calls: Mapped[int] = mapped_column(Integer, default=0)
    success_calls: Mapped[int] = mapped_column(Integer, default=0)
    failed_calls: Mapped[int] = mapped_column(Integer, default=0)
    degraded_calls: Mapped[int] = mapped_column(Integer, default=0)
    total_prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    avg_duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    p90_duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost: Mapped[float] = mapped_column(Float, default=0.0)

    __table_args__ = (
        UniqueConstraint("project_id", "date", "model_name", "task_type", name="uq_model_stats_daily"),
    )
