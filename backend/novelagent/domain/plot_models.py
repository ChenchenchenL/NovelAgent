from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..infrastructure.db import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class PlotThread(Base):
    """Plot thread tracking main arc, subplots, character arcs, and mysteries."""

    __tablename__ = "plot_threads"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    thread_type: Mapped[str] = mapped_column(String(32), default="MAIN")  # MAIN, SUBPLOT, CHARACTER_ARC, MYSTERY
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE")  # ACTIVE, RESOLVED, ABANDONED, SUSPENDED
    priority: Mapped[int] = mapped_column(Integer, default=1)  # 1=主线, 2=重要支线, 3=背景
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    start_scene_id: Mapped[Optional[int]] = mapped_column(ForeignKey("scenes.id"), nullable=True, index=True)
    end_scene_id: Mapped[Optional[int]] = mapped_column(ForeignKey("scenes.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class PlotEvent(Base):
    """Immutable plot event advancing, twisting, delaying, or resolving a plot thread."""

    __tablename__ = "plot_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    plot_thread_id: Mapped[int] = mapped_column(ForeignKey("plot_threads.id"), index=True)
    event_type: Mapped[str] = mapped_column(
        String(32)
    )  # INTRODUCTION, DEVELOPMENT, TWIST, DELAY, RESOLUTION, ABANDONED
    scene_id: Mapped[int] = mapped_column(ForeignKey("scenes.id"), index=True)
    narrative_time: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    description: Mapped[str] = mapped_column(Text)
    evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class Foreshadowing(Base):
    """Foreshadowing setup, development, and payoff lifecycle tracking."""

    __tablename__ = "foreshadowings"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    plot_thread_id: Mapped[Optional[int]] = mapped_column(ForeignKey("plot_threads.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), default="SETUP")  # SETUP, DEVELOP, PAYOFF, ABANDONED
    priority: Mapped[str] = mapped_column(String(16), default="SUBPLOT")  # MAIN, SUBPLOT, BACKGROUND

    # Target window
    target_chapter_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    target_chapter_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    earliest_trigger_chapter: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    latest_payoff_chapter: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Trigger conditions
    trigger_condition_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    trigger_condition_params: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Visibility & Anchors
    visibility: Mapped[str] = mapped_column(String(32), default="AUTHOR")  # READER, CHARACTER, AUTHOR
    visible_to_character_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("characters.id"), nullable=True, index=True
    )
    anchors: Mapped[Optional[list[dict[str, Any]]]] = mapped_column(JSON, default=list)

    # Bound scenes
    setup_scene_id: Mapped[int] = mapped_column(ForeignKey("scenes.id"), index=True)
    payoff_scene_id: Mapped[Optional[int]] = mapped_column(ForeignKey("scenes.id"), nullable=True, index=True)

    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class ImpactNode(Base):
    """Impact graph node representing a trackable narrative entity or event."""

    __tablename__ = "impact_nodes"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    node_type: Mapped[str] = mapped_column(
        String(32)
    )  # SOURCE_SPAN, CLAIM, CHARACTER_EVENT, RELATIONSHIP_EVENT, ITEM_EVENT, PLOT_EVENT, SCENE_REVISION, CHAPTER_OUTPUT, SUMMARY
    entity_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)  # character, item, relationship, plot
    entity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    scene_id: Mapped[Optional[int]] = mapped_column(ForeignKey("scenes.id"), nullable=True, index=True)
    revision_id: Mapped[Optional[int]] = mapped_column(ForeignKey("scene_revisions.id"), nullable=True)
    narrative_time: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class ImpactEdge(Base):
    """Impact graph dependency edge between two narrative nodes."""

    __tablename__ = "impact_edges"
    __table_args__ = (
        UniqueConstraint("project_id", "source_node_id", "target_node_id", "edge_type", name="uq_impact_edge"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    source_node_id: Mapped[int] = mapped_column(ForeignKey("impact_nodes.id"), index=True)
    target_node_id: Mapped[int] = mapped_column(ForeignKey("impact_nodes.id"), index=True)
    edge_type: Mapped[str] = mapped_column(
        String(32)
    )  # DERIVED_FROM, READS, CONTINUES, AFFECTS, SUMMARIZES, FORESHADOWS, PAYS_OFF
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
