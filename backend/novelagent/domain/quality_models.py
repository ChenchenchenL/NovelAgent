from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..infrastructure.db import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class BeatContract(Base):
    """Beat contract defining advancement goals and stop conditions for narrative generation."""

    __tablename__ = "beat_contracts"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    scene_id: Mapped[int] = mapped_column(ForeignKey("scenes.id"), index=True)
    generation_run_id: Mapped[Optional[int]] = mapped_column(ForeignKey("generation_runs.id"), nullable=True)

    required_advancements: Mapped[Optional[list[dict[str, Any]]]] = mapped_column(JSON, default=list)
    stop_conditions: Mapped[Optional[list[dict[str, Any]]]] = mapped_column(JSON, default=list)
    target_word_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_word_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    forbidden_patterns: Mapped[Optional[list[str]]] = mapped_column(JSON, default=list)

    status: Mapped[str] = mapped_column(String(32), default="PENDING")  # PENDING, IN_PROGRESS, COMPLETED, STOPPED, OVERRUN
    advancements_achieved: Mapped[Optional[list[dict[str, Any]]]] = mapped_column(JSON, default=list)
    actual_word_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class ClicheBlacklist(Base):
    """Project-level and genre-specific cliche and model quirk blacklist."""

    __tablename__ = "cliche_blacklist"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    pattern: Mapped[str] = mapped_column(String(500))
    pattern_type: Mapped[str] = mapped_column(String(16), default="EXACT")  # EXACT, REGEX, FUZZY
    category: Mapped[str] = mapped_column(String(32), default="GENERAL")  # GENERAL, EMPTY_OPENING, GENERIC_TRANSITION, MODEL_QUIRK
    genre: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    severity: Mapped[str] = mapped_column(String(16), default="WARNING")  # BLOCKING, WARNING, ADVISORY
    suggestion: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class VoiceLexicon(Base):
    """Character-specific allowed or forbidden vocabulary and tone patterns."""

    __tablename__ = "voice_lexicons"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"), index=True)
    lexicon_type: Mapped[str] = mapped_column(String(16))  # ALLOWED, FORBIDDEN
    entry_type: Mapped[str] = mapped_column(String(32))  # ADDRESS_TERM, PARTICLE, IDIOM, FORBIDDEN_EXPRESSION
    pattern: Mapped[str] = mapped_column(String(500))
    pattern_type: Mapped[str] = mapped_column(String(16), default="EXACT")
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class VoiceFingerprint(Base):
    """Character voice statistics and stylistic fingerprint extracted from canonical text."""

    __tablename__ = "voice_fingerprints"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)

    avg_sentence_length: Mapped[float] = mapped_column(Float, default=15.0)
    sentence_length_std: Mapped[float] = mapped_column(Float, default=5.0)
    colloquial_ratio: Mapped[float] = mapped_column(Float, default=0.0)
    classical_ratio: Mapped[float] = mapped_column(Float, default=0.0)
    honorific_level: Mapped[str] = mapped_column(String(16), default="MEDIUM")
    common_patterns: Mapped[Optional[list[str]]] = mapped_column(JSON, default=list)
    preferred_particles: Mapped[Optional[list[str]]] = mapped_column(JSON, default=list)
    preferred_address_terms: Mapped[Optional[list[str]]] = mapped_column(JSON, default=list)
    preferred_perception_verbs: Mapped[Optional[list[str]]] = mapped_column(JSON, default=list)
    forbidden_expressions: Mapped[Optional[list[str]]] = mapped_column(JSON, default=list)

    source_revision_ids: Mapped[Optional[list[int]]] = mapped_column(JSON, default=list)
    source_text_sample_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class QualityReport(Base):
    """Scene quality check report recording detected issues, severity, and root causes."""

    __tablename__ = "quality_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    scene_id: Mapped[int] = mapped_column(ForeignKey("scenes.id"), index=True)
    revision_id: Mapped[Optional[int]] = mapped_column(ForeignKey("scene_revisions.id"), nullable=True)

    issues: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    summary: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class AuthorFeedback(Base):
    """Author acceptance, rejection, or ignore feedback on quality check issues."""

    __tablename__ = "author_feedback"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    issue_type: Mapped[str] = mapped_column(String(32))
    decision: Mapped[str] = mapped_column(String(16))  # ACCEPT, REJECT, IGNORE
    scope: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)  # ONCE, THIS_SCENE, THIS_CHAPTER, ALWAYS
    expiry_scene_id: Mapped[Optional[int]] = mapped_column(ForeignKey("scenes.id"), nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    scene_id: Mapped[Optional[int]] = mapped_column(ForeignKey("scenes.id"), nullable=True)
    revision_id: Mapped[Optional[int]] = mapped_column(ForeignKey("scene_revisions.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
