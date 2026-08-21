from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


# --- Beat Schemas ---
class BeatCreate(BaseModel):
    required_advancements: list[dict[str, Any]] = Field(default_factory=list)
    stop_conditions: list[dict[str, Any]] = Field(default_factory=list)
    target_word_count: Optional[int] = Field(default=None, ge=10, le=50000)
    max_word_count: Optional[int] = Field(default=None, ge=10, le=100000)
    forbidden_patterns: list[str] = Field(default_factory=list)
    generation_run_id: Optional[int] = None


class BeatUpdate(BaseModel):
    required_advancements: Optional[list[dict[str, Any]]] = None
    stop_conditions: Optional[list[dict[str, Any]]] = None
    target_word_count: Optional[int] = Field(default=None, ge=10, le=50000)
    max_word_count: Optional[int] = Field(default=None, ge=10, le=100000)
    forbidden_patterns: Optional[list[str]] = None


class BeatAdvanceRequest(BaseModel):
    advancement: dict[str, Any]


class BeatStopRequest(BaseModel):
    reason: str = "MANUAL_STOP"
    actual_word_count: Optional[int] = Field(default=None, ge=0)


class BeatView(BaseModel):
    id: int
    project_id: int
    scene_id: int
    generation_run_id: Optional[int] = None
    required_advancements: list[dict[str, Any]]
    stop_conditions: list[dict[str, Any]]
    target_word_count: Optional[int] = None
    max_word_count: Optional[int] = None
    forbidden_patterns: list[str]
    status: str
    advancements_achieved: list[dict[str, Any]]
    actual_word_count: int
    created_at: str


# --- Cliche Blacklist Schemas ---
class ClicheCreate(BaseModel):
    pattern: str = Field(..., min_length=1, max_length=500)
    pattern_type: str = Field(default="EXACT", pattern="^(EXACT|REGEX|FUZZY)$")
    category: str = Field(default="GENERAL")
    genre: Optional[str] = None
    severity: str = Field(default="WARNING", pattern="^(BLOCKING|WARNING|ADVISORY)$")
    suggestion: Optional[str] = None
    enabled: bool = True


class ClicheUpdate(BaseModel):
    pattern: Optional[str] = Field(default=None, min_length=1, max_length=500)
    pattern_type: Optional[str] = Field(default=None, pattern="^(EXACT|REGEX|FUZZY)$")
    category: Optional[str] = None
    genre: Optional[str] = None
    severity: Optional[str] = Field(default=None, pattern="^(BLOCKING|WARNING|ADVISORY)$")
    suggestion: Optional[str] = None
    enabled: Optional[bool] = None


class ClicheView(BaseModel):
    id: int
    project_id: int
    pattern: str
    pattern_type: str
    category: str
    genre: Optional[str] = None
    severity: str
    suggestion: Optional[str] = None
    version: int
    enabled: bool
    created_at: str


class ClicheScanRequest(BaseModel):
    text: str = Field(..., min_length=1)
    genre: Optional[str] = None


# --- Voice Fingerprint & Lexicon Schemas ---
class VoiceLexiconCreate(BaseModel):
    character_id: int
    lexicon_type: str = Field(..., pattern="^(ALLOWED|FORBIDDEN)$")
    entry_type: str = Field(default="ADDRESS_TERM")
    pattern: str = Field(..., min_length=1, max_length=500)
    pattern_type: str = Field(default="EXACT", pattern="^(EXACT|REGEX)$")


class VoiceLexiconView(BaseModel):
    id: int
    project_id: int
    character_id: int
    lexicon_type: str
    entry_type: str
    pattern: str
    pattern_type: str
    version: int
    created_at: str


class VoiceFingerprintCreate(BaseModel):
    avg_sentence_length: float = Field(..., ge=1.0, le=500.0)
    sentence_length_std: float = Field(..., ge=0.0, le=200.0)
    colloquial_ratio: float = Field(default=0.0, ge=0.0, le=100.0)
    classical_ratio: float = Field(default=0.0, ge=0.0, le=100.0)
    honorific_level: str = Field(default="MEDIUM")
    preferred_particles: list[str] = Field(default_factory=list)
    forbidden_expressions: list[str] = Field(default_factory=list)


class VoiceFingerprintView(BaseModel):
    id: int
    project_id: int
    character_id: int
    version: int
    avg_sentence_length: float
    sentence_length_std: float
    colloquial_ratio: float
    classical_ratio: float
    honorific_level: str
    common_patterns: list[str]
    preferred_particles: list[str]
    preferred_address_terms: list[str]
    preferred_perception_verbs: list[str]
    forbidden_expressions: list[str]
    source_revision_ids: list[int]
    source_text_sample_count: int
    created_at: str
    updated_at: str


class VoiceDriftCheckRequest(BaseModel):
    character_id: int
    text: str = Field(..., min_length=1)


# --- Quality Report Schemas ---
class QualityCheckRequest(BaseModel):
    text_content: Optional[str] = None
    genre: Optional[str] = None


class QualityReportView(BaseModel):
    id: int
    project_id: int
    scene_id: int
    revision_id: Optional[int] = None
    issues: list[dict[str, Any]]
    summary: dict[str, Any]
    generated_at: str


# --- Author Feedback Schemas ---
class AuthorFeedbackCreate(BaseModel):
    issue_type: str
    decision: str = Field(..., pattern="^(ACCEPT|REJECT|IGNORE)$")
    scope: str = Field(default="ONCE", pattern="^(ONCE|THIS_SCENE|THIS_CHAPTER|ALWAYS)$")
    expiry_scene_id: Optional[int] = None
    reason: Optional[str] = None
    scene_id: Optional[int] = None
    revision_id: Optional[int] = None


class AuthorFeedbackView(BaseModel):
    id: int
    project_id: int
    issue_type: str
    decision: str
    scope: str
    expiry_scene_id: Optional[int] = None
    reason: Optional[str] = None
    scene_id: Optional[int] = None
    revision_id: Optional[int] = None
    created_at: str
