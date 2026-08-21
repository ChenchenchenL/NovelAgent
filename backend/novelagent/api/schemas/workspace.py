from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field


class PatchCreate(BaseModel):
    base_revision_id: Optional[int] = None
    content: str
    source: Literal["AUTHOR", "AI"] = "AUTHOR"


class WorkspaceUpdate(BaseModel):
    draft_content: Optional[str] = None
    cursor_position: Optional[int] = None
    selection_start: Optional[int] = None
    selection_end: Optional[int] = None
    undo_stack: Optional[list] = None
    redo_stack: Optional[list] = None
    auto_save_snapshot: Optional[dict] = None
    status: Optional[str] = None


class WorkspaceView(BaseModel):
    id: int
    scene_id: int
    base_revision_id: Optional[int] = None
    draft_content: str = ""
    cursor_position: int = 0
    selection_start: Optional[int] = None
    selection_end: Optional[int] = None
    status: str = "DRAFT"
    auto_save_snapshot: Optional[dict] = None
    undo_stack: list = Field(default_factory=list)
    redo_stack: list = Field(default_factory=list)
    updated_at: Optional[str] = None


class TextPatch(BaseModel):
    base_revision_id: Optional[int] = None
    range_start: int
    range_end: int
    new_content: str = ""
    source: str = "AUTHOR"
    intent: str = "edit"


class PatchApplyResponse(BaseModel):
    revision_id: int
    status: str = "DRAFT"
    applied_range: dict


class PatchesMergeRequest(BaseModel):
    base_revision_id: Optional[int] = None
    patches: list[TextPatch]


class PatchesSelectiveAcceptRequest(BaseModel):
    base_revision_id: Optional[int] = None
    patches: list[TextPatch]


class RevisionDiffView(BaseModel):
    base_revision_id: Optional[int] = None
    target_revision_id: int
    unified_diff: str
    additions: int
    deletions: int
    chunks: list[dict] = Field(default_factory=list)
