from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class ItemTransition:
    event_type: str
    from_holder: str | None
    to_holder: str | None


@dataclass(frozen=True)
class TextPatchData:
    range_start: int
    range_end: int
    new_content: str = ""
    base_revision_id: int | None = None
    source: str = "AUTHOR"
    intent: str = "edit"


@dataclass(frozen=True)
class SourceSpan:
    revision_id: int | None
    start_offset: int
    end_offset: int
    content_hash: str | None = None

    def resolve_text(self, text_provider_or_content: Any) -> str:
        """Resolve text slice either from full string or revision object with content."""
        if isinstance(text_provider_or_content, str):
            return text_provider_or_content[self.start_offset:self.end_offset]
        if hasattr(text_provider_or_content, "content") and text_provider_or_content.content:
            return text_provider_or_content.content[self.start_offset:self.end_offset]
        return ""


@dataclass(frozen=True)
class WorkspaceUpdateData:
    draft_content: str | None = None
    cursor_position: int | None = None
    selection_start: int | None = None
    selection_end: int | None = None
    undo_stack: list | None = None
    redo_stack: list | None = None
    auto_save_snapshot: dict | None = None
    status: str | None = None


ALLOWED_ITEM_EVENTS = {
    "CREATED",
    "TRANSFERRED",
    "HIDDEN",
    "LOST",
    "FOUND",
    "DESTROYED",
}


def validate_item_transition(
    *,
    current_state: str,
    current_holder: str | None,
    transition: ItemTransition,
    unique_item: bool,
) -> str:
    """Validate conservation before a confirmed ItemEvent is written."""
    if transition.event_type not in ALLOWED_ITEM_EVENTS:
        raise ValueError(f"unknown item event: {transition.event_type}")
    if transition.event_type == "TRANSFERRED":
        if current_state in {"DESTROYED", "LOST"}:
            raise ValueError("a destroyed or lost item cannot be transferred")
        if transition.from_holder != current_holder:
            raise ValueError("item transfer source does not match current holder")
        if not transition.to_holder:
            raise ValueError("item transfer requires a destination holder")
        return "HELD"
    if transition.event_type == "CREATED":
        if current_state != "CREATED" and unique_item:
            raise ValueError("unique item cannot be created twice")
        return "HELD" if transition.to_holder else "CREATED"
    if transition.event_type == "DESTROYED":
        return "DESTROYED"
    if transition.event_type in {"HIDDEN", "LOST"}:
        return transition.event_type
    if transition.event_type == "FOUND":
        if current_state != "LOST":
            raise ValueError("only a lost item can be found")
        return "HELD"
    return current_state


def claim_is_low_risk(
    *,
    modality: str,
    subject_resolved: bool,
    predicate: str,
    explicit: bool = True,
    confidence: float = 1.0,
    entity_confidence: float = 1.0,
) -> bool:
    """Only explicit ACTUAL entity/property/location claims auto-confirm."""
    if modality != "ACTUAL":
        return False
    if not subject_resolved or not explicit:
        return False
    if confidence < 0.80 or entity_confidence < 0.75:
        return False
    return predicate in {"appears", "has_attribute", "located_at"}



VALID_CHAPTER_TRANSITIONS: dict[str, set[str]] = {
    "IDEA": {"OUTLINED"},
    "OUTLINED": {"IN_PROGRESS", "IDEA"},
    "IN_PROGRESS": {"READY_FOR_REVIEW", "LOCALLY_STALE"},
    "READY_FOR_REVIEW": {"RELEASED", "IN_PROGRESS"},
    "LOCALLY_STALE": {"IN_PROGRESS", "READY_FOR_REVIEW"},
    "RELEASED": {"IN_PROGRESS"},
}


def validate_chapter_status_transition(
    current_status: str,
    new_status: str,
    scene_statuses: list[str],
) -> None:
    """Validate Chapter state transition according to phase 1 PRD state machine."""
    if current_status not in VALID_CHAPTER_TRANSITIONS:
        raise ValueError(f"未知当前章节状态: {current_status}")
    if new_status not in VALID_CHAPTER_TRANSITIONS[current_status]:
        raise ValueError(f"非法章节状态流转: {current_status} -> {new_status}")
    if new_status == "READY_FOR_REVIEW":
        if not scene_statuses or not any(s == "SCENE_ACCEPTED" for s in scene_statuses):
            raise ValueError("流转至 READY_FOR_REVIEW 需至少有一个场景处于 SCENE_ACCEPTED 状态")
    elif new_status == "RELEASED":
        if not scene_statuses or not all(s == "SCENE_ACCEPTED" for s in scene_statuses):
            raise ValueError("流转至 RELEASED 需所有场景均处于 SCENE_ACCEPTED 状态")


VALID_SCENE_TRANSITIONS: dict[str, set[str]] = {
    "PLANNED": {"WRITING"},
    "WRITING": {"PARTIALLY_ACCEPTED", "SCENE_ACCEPTED", "EXTRACTION_PENDING"},
    "PARTIALLY_ACCEPTED": {"WRITING", "SCENE_ACCEPTED", "EXTRACTION_PENDING"},
    "EXTRACTION_PENDING": {"SCENE_ACCEPTED", "WRITING"},
    "SCENE_ACCEPTED": {"WRITING"},
}


def validate_scene_status_transition(
    current_status: str,
    new_status: str,
    has_content: bool = True,
) -> None:
    """Validate Scene state transition according to phase 1 PRD state machine."""
    if current_status not in VALID_SCENE_TRANSITIONS:
        raise ValueError(f"未知当前场景状态: {current_status}")
    if new_status not in VALID_SCENE_TRANSITIONS[current_status]:
        raise ValueError(f"非法场景状态流转: {current_status} -> {new_status}")
    if current_status == "WRITING" and new_status in {"PARTIALLY_ACCEPTED", "SCENE_ACCEPTED", "EXTRACTION_PENDING"}:
        if not has_content:
            raise ValueError("场景无正文内容，无法流转至采纳或抽取状态")
