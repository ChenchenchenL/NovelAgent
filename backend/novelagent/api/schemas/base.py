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


class VolumeCreate(BaseModel):
    title: str
    status: Optional[str] = None


class VolumeUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None


class ChapterCreate(BaseModel):
    title: str
    volume_id: Optional[int] = None
    status: Optional[str] = None
    contract: Optional[dict] = None


class ChapterUpdate(BaseModel):
    title: Optional[str] = None
    volume_id: Optional[int] = None
    order_in_volume: Optional[int] = None
    contract: Optional[dict] = None
    status: Optional[str] = None


class ReorderRequest(BaseModel):
    type: str
    parent_id: Optional[int] = None
    order: list[int] = Field(default_factory=list)


class ChapterStatusUpdate(BaseModel):
    status: str


class SceneCreate(BaseModel):
    title: str
    pov: Optional[str] = None
    location: Optional[str] = None


class SceneUpdate(BaseModel):
    title: Optional[str] = None
    pov: Optional[str] = None
    location: Optional[str] = None
    order_in_chapter: Optional[int] = None


class SceneStatusUpdate(BaseModel):
    status: str


class SceneContractUpdate(BaseModel):
    pov: Optional[str] = None
    location: Optional[str] = None
    entry_contract: Optional[dict] = None
    exit_contract: Optional[dict] = None


class SceneEntryContractUpdate(BaseModel):
    entry_contract: Optional[dict] = None
    goal: Optional[str] = None
    emotional_state: Optional[str] = None
    knowledge: Optional[str] = None


class SceneExitStateUpdate(BaseModel):
    exit_state: Optional[dict] = None
    outcome: Optional[str] = None
    emotional_shift: Optional[str] = None
    unresolved: Optional[str] = None


class SceneReorderRequest(BaseModel):
    scene_ids: list[int]


class ChapterReorderRequest(BaseModel):
    chapter_ids: list[int]


class ReorderRequest(BaseModel):
    type: str
    parent_id: Optional[int] = None
    order: list[int]


class ProjectView(BaseModel):
    id: int
    name: str


class VolumeView(BaseModel):
    id: int
    project_id: int
    title: str
    sequence: int = 1
    order_in_project: Optional[int] = None
    status: Optional[str] = "IDEA"
    created_at: Optional[str] = None


class ChapterView(BaseModel):
    id: int
    project_id: int
    volume_id: Optional[int] = None
    title: str
    sequence: int = 1
    order_in_volume: Optional[int] = None
    status: str = "IDEA"
    contract: Optional[dict] = None
    created_at: Optional[str] = None


class SceneView(BaseModel):
    id: int
    chapter_id: int
    title: str
    sequence: int = 1
    order_in_chapter: Optional[int] = None
    pov: Optional[str] = None
    location: Optional[str] = None
    entry_contract: Optional[dict] = None
    exit_contract: Optional[dict] = None
    status: str = "PLANNED"
    current_revision_id: Optional[int] = None
    has_active_generation_run: bool = False
    has_pending_extraction: bool = False
    created_at: Optional[str] = None


class RevisionView(BaseModel):
    id: int
    scene_id: int
    version_number: Optional[int] = None
    content: str = ""
    content_hash: str = ""
    word_count: Optional[int] = None
    source: str = "AUTHOR"
    patch_info: Optional[dict] = None
    created_at: Optional[str] = None


class ChapterDetailView(BaseModel):
    id: int
    project_id: int
    volume_id: Optional[int] = None
    title: str
    sequence: int = 1
    order_in_volume: Optional[int] = None
    status: str = "IDEA"
    contract: Optional[dict] = None
    scenes: list[SceneView] = Field(default_factory=list)
    created_at: Optional[str] = None


class SceneDetailView(BaseModel):
    id: int
    chapter_id: int
    title: str
    sequence: int = 1
    order_in_chapter: Optional[int] = None
    pov: Optional[str] = None
    location: Optional[str] = None
    entry_contract: Optional[dict] = None
    exit_contract: Optional[dict] = None
    status: str = "PLANNED"
    current_revision_id: Optional[int] = None
    content: str = ""
    revisions: list[RevisionView] = Field(default_factory=list)
    created_at: Optional[str] = None


class ProjectTreeView(BaseModel):
    volumes: list[dict] = Field(default_factory=list)
    unassigned_chapters: list[dict] = Field(default_factory=list)
    project: Optional[ProjectView] = None


