from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, LargeBinary, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..infrastructure.db import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class FTSDocument(Base):
    """Full-text search document storing searchable text from scenes, claims, and summaries."""

    __tablename__ = "fts_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    doc_type: Mapped[str] = mapped_column(String(32))  # SCENE, CLAIM, SUMMARY
    source_id: Mapped[int] = mapped_column(Integer)
    source_version: Mapped[int] = mapped_column(Integer, default=1)
    content: Mapped[str] = mapped_column(Text)
    narrative_time: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    modality: Mapped[str] = mapped_column(String(32), default="ACTUAL")
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class VectorDocument(Base):
    """Vectorized document metadata tracking source version and modality."""

    __tablename__ = "vector_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    doc_type: Mapped[str] = mapped_column(String(32))  # SCENE, CLAIM, SUMMARY
    source_id: Mapped[int] = mapped_column(Integer)
    source_version: Mapped[int] = mapped_column(Integer, default=1)
    content: Mapped[str] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64))
    narrative_time: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    modality: Mapped[str] = mapped_column(String(32), default="ACTUAL")
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class VectorEmbedding(Base):
    """Embedding vector storage associated with a VectorDocument."""

    __tablename__ = "vector_embeddings"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("vector_documents.id"), index=True)
    model_name: Mapped[str] = mapped_column(String(255))
    vector_data: Mapped[bytes] = mapped_column(LargeBinary)
    vector_dim: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class KGNode(Base):
    """Knowledge Graph projection node representing a canon entity or state."""

    __tablename__ = "kg_nodes"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    node_type: Mapped[str] = mapped_column(String(32))  # CHARACTER, ITEM, LOCATION, EVENT, SECRET
    entity_id: Mapped[int] = mapped_column(Integer, index=True)
    name: Mapped[str] = mapped_column(String(255))
    narrative_time: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    modality: Mapped[str] = mapped_column(String(32), default="ACTUAL")
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class KGEdge(Base):
    """Knowledge Graph projection edge representing relationships, possession, location, or knowledge."""

    __tablename__ = "kg_edges"
    __table_args__ = (
        UniqueConstraint("project_id", "source_node_id", "target_node_id", "edge_type", "narrative_time", name="uq_kg_edge"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    source_node_id: Mapped[int] = mapped_column(ForeignKey("kg_nodes.id"), index=True)
    target_node_id: Mapped[int] = mapped_column(ForeignKey("kg_nodes.id"), index=True)
    edge_type: Mapped[str] = mapped_column(String(32))  # RELATIONSHIP, HOLDS, LOCATED_AT, KNOWS, FORESHADOWS
    narrative_time: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    modality: Mapped[str] = mapped_column(String(32), default="ACTUAL")
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    source_scene_id: Mapped[Optional[int]] = mapped_column(ForeignKey("scenes.id"), nullable=True)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class SummaryArtifact(Base):
    """Hierarchical summary artifact representing project, volume, chapter, scene, or character summary."""

    __tablename__ = "summary_artifacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    summary_type: Mapped[str] = mapped_column(String(32))  # PROJECT, VOLUME, PLOT_THREAD, CHARACTER, CHAPTER, SCENE
    source_id: Mapped[int] = mapped_column(Integer)
    source_version: Mapped[int] = mapped_column(Integer, default=1)
    content: Mapped[str] = mapped_column(Text)
    covered_node_ids: Mapped[Optional[list[int]]] = mapped_column(JSON, default=list)
    narrative_time_range: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)
