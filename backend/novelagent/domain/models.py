from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..infrastructure.db import Base


def now() -> datetime:
    return datetime.now(timezone.utc)


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(primary_key=True)
    path: Mapped[str] = mapped_column(String(1024), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Volume(Base):
    __tablename__ = "volumes"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    sequence: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(32), default="IDEA")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Chapter(Base):
    __tablename__ = "chapters"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    volume_id: Mapped[Optional[int]] = mapped_column(ForeignKey("volumes.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    sequence: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(32), default="IDEA")
    contract: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Scene(Base):
    __tablename__ = "scenes"
    id: Mapped[int] = mapped_column(primary_key=True)
    chapter_id: Mapped[int] = mapped_column(ForeignKey("chapters.id"), index=True)
    title: Mapped[str] = mapped_column(String(255), default="未命名场景")
    sequence: Mapped[int] = mapped_column(Integer, default=1)
    pov: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    current_revision_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("scene_revisions.id", ondelete="SET NULL", use_alter=True, name="fk_scenes_current_revision_id"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(32), default="PLANNED")
    entry_contract: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    exit_state: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class SceneRevision(Base):
    __tablename__ = "scene_revisions"
    id: Mapped[int] = mapped_column(primary_key=True)
    scene_id: Mapped[int] = mapped_column(ForeignKey("scenes.id"), index=True)
    base_revision_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    content: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(String(32), default="AUTHOR")
    content_hash: Mapped[str] = mapped_column(String(64))
    patch_info: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class GenerationWorkspace(Base):
    __tablename__ = "generation_workspaces"
    __table_args__ = (UniqueConstraint("scene_id", name="uq_generation_workspaces_scene_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    scene_id: Mapped[int] = mapped_column(ForeignKey("scenes.id"), index=True)
    base_revision_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    draft_content: Mapped[str] = mapped_column(Text, default="")
    cursor_position: Mapped[int] = mapped_column(Integer, default=0)
    selection_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    selection_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="DRAFT")
    auto_save_snapshot: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    undo_stack: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    redo_stack: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    context_manifest: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)


class ClaimCandidate(Base):
    __tablename__ = "claim_candidates"
    id: Mapped[int] = mapped_column(primary_key=True)
    scene_id: Mapped[int] = mapped_column(ForeignKey("scenes.id"), index=True)
    subject: Mapped[str] = mapped_column(String(255))
    predicate: Mapped[str] = mapped_column(String(255))
    object_value: Mapped[str] = mapped_column(String(255))
    modality: Mapped[str] = mapped_column(String(32), default="AMBIGUOUS")
    cognitive_subject: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_start: Mapped[int] = mapped_column(Integer, default=0)
    source_end: Mapped[int] = mapped_column(Integer, default=0)
    paragraph_index: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source_text: Mapped[str] = mapped_column(Text, default="")
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    confidence: Mapped[float] = mapped_column(default=0.0)
    entity_confidence: Mapped[float] = mapped_column(default=0.0)
    hypothesis_tags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="REVIEW_REQUIRED")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class CanonClaim(Base):
    __tablename__ = "canon_claims"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    subject: Mapped[str] = mapped_column(String(255))
    predicate: Mapped[str] = mapped_column(String(255))
    object_value: Mapped[str] = mapped_column(String(255))
    modality: Mapped[str] = mapped_column(String(32), default="ACTUAL")
    source_scene_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    source_start: Mapped[int] = mapped_column(Integer, default=0)
    source_end: Mapped[int] = mapped_column(Integer, default=0)
    source_candidate_id: Mapped[Optional[int]] = mapped_column(ForeignKey("claim_candidates.id", ondelete="SET NULL"), nullable=True)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=True)
    auto_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    author_decision_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)


class EntityAlias(Base):
    __tablename__ = "entity_aliases"
    __table_args__ = (UniqueConstraint("project_id", "canonical_name", "alias_name", name="uq_project_canonical_alias"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    canonical_name: Mapped[str] = mapped_column(String(255))
    alias_name: Mapped[str] = mapped_column(String(255))
    alias_type: Mapped[str] = mapped_column(String(32), default="informal")
    confirmed_by: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class ItemEntity(Base):
    __tablename__ = "items"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    unique_item: Mapped[bool] = mapped_column(Boolean, default=False)
    current_holder: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    current_state: Mapped[str] = mapped_column(String(32), default="CREATED")


class ItemEvent(Base):
    __tablename__ = "item_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(32))
    from_holder: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    to_holder: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    scene_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)


class ShadowEntity(Base):
    __tablename__ = "shadow_entities"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    display_name: Mapped[str] = mapped_column(String(255))
    canonical_character: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    revealed_scene_id: Mapped[Optional[int]] = mapped_column(nullable=True)


class ImportJob(Base):
    __tablename__ = "import_jobs"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    source_path: Mapped[str] = mapped_column(String(1024))
    status: Mapped[str] = mapped_column(String(32), default="PENDING")
    checkpoint: Mapped[int] = mapped_column(Integer, default=0)
    total_files: Mapped[int] = mapped_column(Integer, default=0)
    total_batches: Mapped[int] = mapped_column(Integer, default=0)
    batch_size: Mapped[int] = mapped_column(Integer, default=10)
    auto_extract: Mapped[bool] = mapped_column(Boolean, default=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)
    error_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class ImportCheckpoint(Base):
    __tablename__ = "import_checkpoints"
    __table_args__ = (UniqueConstraint("job_id", "batch_index", name="uq_import_checkpoints_job_batch"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("import_jobs.id", ondelete="CASCADE"), index=True)
    batch_index: Mapped[int] = mapped_column(Integer)
    file_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    batch_info: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    items_imported: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(32), default="PENDING")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class ModelInvocation(Base):
    __tablename__ = "model_invocations"
    id: Mapped[int] = mapped_column(primary_key=True)
    task_type: Mapped[str] = mapped_column(String(64))
    tier: Mapped[str] = mapped_column(String(8))
    model: Mapped[str] = mapped_column(String(255))
    endpoint: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    context_manifest: Mapped[dict] = mapped_column(JSON, default=dict)
    token_usage: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    degraded_to: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="PENDING")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class CommitJournal(Base):
    __tablename__ = "commit_journal"
    id: Mapped[int] = mapped_column(primary_key=True)
    revision_id: Mapped[int] = mapped_column(Integer)
    content_hash: Mapped[str] = mapped_column(String(64))
    file_path: Mapped[str] = mapped_column(String(1024))
    file_status: Mapped[str] = mapped_column(String(32), default="PENDING")
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    encoding: Mapped[str] = mapped_column(String(32), default="utf-8")
    recovery_attempts: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class PendingProjection(Base):
    __tablename__ = "pending_projections"
    id: Mapped[int] = mapped_column(primary_key=True)
    revision_id: Mapped[int] = mapped_column(Integer)
    projection_type: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), default="PENDING")


class GenerationRun(Base):
    __tablename__ = "generation_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    scene_id: Mapped[int] = mapped_column(ForeignKey("scenes.id"), index=True)
    task_type: Mapped[str] = mapped_column(String(64), default="paragraph_generation")
    status: Mapped[str] = mapped_column(String(32), default="CREATED")
    prompt: Mapped[str] = mapped_column(Text, default="")
    request_snapshot: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    response_snapshot: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    model_tier: Mapped[str] = mapped_column(String(8), default="T3")
    actual_model: Mapped[str] = mapped_column(String(255), default="")
    context_manifest: Mapped[dict] = mapped_column(JSON, default=dict)
    token_usage: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    retries: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class GenerationRunEvent(Base):
    __tablename__ = "generation_run_events"
    __table_args__ = (UniqueConstraint("run_id", "sequence_number", name="uq_generation_run_events_seq"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("generation_runs.id", ondelete="CASCADE"), index=True)
    event_type: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    sequence_number: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
