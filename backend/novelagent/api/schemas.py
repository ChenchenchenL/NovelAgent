from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

Modality = Literal[
    "ACTUAL",
    "BELIEVED",
    "REPORTED",
    "REMEMBERED",
    "DREAMED",
    "HYPOTHETICAL",
    "COUNTERFACTUAL",
    "METAPHORICAL",
    "AMBIGUOUS",
]


class DirectorySelection(BaseModel):
    current_path: str
    history_paths: list[str] = Field(default_factory=list)


class ProjectOpen(BaseModel):
    path: str


class ImportRequest(BaseModel):
    source_path: str


class PatchCreate(BaseModel):
    base_revision_id: Optional[int] = None
    content: str
    source: Literal["AUTHOR", "AI"] = "AUTHOR"


class ClaimDecision(BaseModel):
    decision: Literal["CONFIRM", "REJECT", "DEFER"]


class GenerateRequest(BaseModel):
    instruction: str = "继续当前场景"
    tier: Literal["T1", "T2", "T3"] = "T2"


class ModelSettingsRequest(BaseModel):
    endpoint: str
    models: dict[str, str] = Field(default_factory=dict)
    api_key: Optional[str] = None


class ClaimView(BaseModel):
    id: int
    subject: str
    predicate: str
    object_value: str
    modality: Modality
    source_start: int
    source_end: int
    source_text: str
    confidence: float
    entity_confidence: float
    status: str


class ProjectView(BaseModel):
    id: int
    name: str
    path: str


class VolumeCreate(BaseModel):
    title: str
    status: Optional[str] = "IDEA"


class VolumeUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None


class VolumeView(BaseModel):
    id: int
    project_id: int
    title: str
    sequence: int
    status: str
    created_at: str


class ChapterCreate(BaseModel):
    title: str
    volume_id: Optional[int] = None
    status: Optional[str] = "IDEA"
    contract: Optional[dict] = None


class ChapterUpdate(BaseModel):
    title: Optional[str] = None
    volume_id: Optional[int] = None
    contract: Optional[dict] = None


class ChapterStatusUpdate(BaseModel):
    status: str


class ChapterView(BaseModel):
    id: int
    project_id: int
    volume_id: Optional[int]
    title: str
    sequence: int
    status: str
    contract: Optional[dict] = None


class SceneCreate(BaseModel):
    title: Optional[str] = "未命名场景"
    pov: Optional[str] = None
    location: Optional[str] = None


class SceneUpdate(BaseModel):
    title: Optional[str] = None
    pov: Optional[str] = None
    location: Optional[str] = None


class SceneStatusUpdate(BaseModel):
    status: str


class SceneEntryContractUpdate(BaseModel):
    entry_contract: dict


class SceneExitStateUpdate(BaseModel):
    exit_state: dict


class RevisionView(BaseModel):
    id: int
    scene_id: int
    base_revision_id: Optional[int]
    content: str = ""
    source: str
    content_hash: str
    patch_info: Optional[dict] = None
    created_at: str


class SceneView(BaseModel):
    id: int
    chapter_id: int
    title: str
    sequence: int = 1
    pov: Optional[str] = None
    location: Optional[str] = None
    status: str
    current_revision_id: Optional[int]
    content: str = ""
    entry_contract: Optional[dict] = None
    exit_state: Optional[dict] = None


class ChapterDetailView(BaseModel):
    id: int
    project_id: int
    volume_id: Optional[int]
    title: str
    sequence: int
    status: str
    contract: Optional[dict] = None
    scenes: list[SceneView] = Field(default_factory=list)


class ReorderRequest(BaseModel):
    type: Literal["volume", "chapter", "scene"]
    parent_id: Optional[int] = None
    order: list[int]


class ProjectTreeView(BaseModel):
    volumes: list[dict] = Field(default_factory=list)
    unassigned_chapters: list[dict] = Field(default_factory=list)


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

