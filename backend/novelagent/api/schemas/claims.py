from __future__ import annotations

from typing import Any, Literal, Optional
from pydantic import BaseModel, Field
from .base import Modality


class ClaimCandidateInput(BaseModel):
    subject: str = Field(..., min_length=1, max_length=255)
    predicate: str = Field(..., max_length=255)
    object_value: str = Field(..., max_length=255)
    modality: Modality = "AMBIGUOUS"
    cognitive_subject: Optional[str] = None
    source_start: int = Field(0, ge=0)
    source_end: int = Field(0, ge=0)
    paragraph_index: Optional[int] = None
    source_text: str = Field("", max_length=2000)
    content_hash: Optional[str] = None
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    entity_confidence: float = Field(0.0, ge=0.0, le=1.0)
    hypothesis_tags: Optional[list[str]] = None


class ClaimView(BaseModel):
    id: int
    subject: str
    predicate: str
    object_value: str
    modality: Modality
    cognitive_subject: Optional[str] = None
    source_start: int
    source_end: int
    paragraph_index: Optional[int] = None
    source_text: str
    confidence: float
    entity_confidence: float
    status: str
    created_at: Optional[str] = None


class CanonClaimView(BaseModel):
    id: int
    project_id: int
    subject: str
    predicate: str
    object_value: str
    modality: Modality
    source_scene_id: Optional[int] = None
    source_start: int
    source_end: int
    source_candidate_id: Optional[int] = None
    confirmed: bool = True
    auto_confirmed: bool = False
    author_decision_notes: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ClaimDecision(BaseModel):
    decision: Literal["CONFIRM", "REJECT", "DEFER"]
    corrections: Optional[dict[str, Any]] = None
    notes: Optional[str] = None


class BatchClaimDecisionRequest(BaseModel):
    decisions: list[dict[str, Any]]


class ClaimExtractRequest(BaseModel):
    revision_id: Optional[int] = None
    force_full_scan: bool = False


class EntityAliasCreate(BaseModel):
    canonical_name: str
    alias_name: str
    alias_type: str = "informal"
    confirmed_by: bool = True


class EntityAliasView(BaseModel):
    id: int
    project_id: int
    canonical_name: str
    alias_name: str
    alias_type: str
    confirmed_by: bool
    created_at: str
