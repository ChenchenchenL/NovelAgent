from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional


@dataclass(frozen=True)
class ItemTransition:
    event_type: str
    from_holder: str | None = None
    to_holder: str | None = None
    from_location: str | None = None
    to_location: str | None = None
    narrative_time: str | None = None


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
    if current_state == "DESTROYED":
        raise ValueError("a destroyed item cannot be transferred, lost, found or modified")

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

    if transition.event_type == "HIDDEN":
        if current_state not in {"HELD", "CREATED"}:
            raise ValueError("only an item in hand or created can be hidden")
        return "HIDDEN"

    if transition.event_type == "LOST":
        if current_state not in {"HELD", "HIDDEN"}:
            raise ValueError("only a held or hidden item can be lost")
        return "LOST"

    if transition.event_type == "FOUND":
        if current_state not in {"LOST", "HIDDEN"}:
            raise ValueError("only a lost or hidden item can be found")
        if not transition.to_holder:
            raise ValueError("finding an item requires a discoverer/holder")
        return "HELD"

    if transition.event_type == "DESTROYED":
        return "DESTROYED"

    return current_state


def calculate_time_delta_minutes(departure_time: str | None, arrival_time: str | None) -> int | None:
    """Calculate minutes between two times supporting ISO timestamps or numeric strings."""
    if not departure_time or not arrival_time:
        return None
    try:
        d_val = int(departure_time)
        a_val = int(arrival_time)
        return max(0, abs(a_val - d_val))
    except (ValueError, TypeError):
        pass
    try:
        d_dt = datetime.fromisoformat(departure_time.replace("Z", "+00:00"))
        a_dt = datetime.fromisoformat(arrival_time.replace("Z", "+00:00"))
        delta_sec = (a_dt - d_dt).total_seconds()
        return max(0, int(delta_sec // 60))
    except Exception:
        return None


def evaluate_movement_feasibility(
    from_location_id: int,
    to_location_id: int,
    travel_mode: str,
    min_duration_minutes: int | None,
    actual_duration_minutes: int | None,
) -> dict[str, Any]:
    """Evaluate feasibility of movement given travel profile and duration."""
    if from_location_id == to_location_id:
        return {"status": "OK", "duration": 0, "reason": "same_location"}

    if travel_mode in {"TELEPORT", "FLIGHT"}:
        return {"status": "OK", "duration": actual_duration_minutes or 0, "reason": "supernatural_or_instant_travel"}

    if min_duration_minutes is None:
        return {"status": "UNKNOWN", "reason": "no travel profile defined"}

    if actual_duration_minutes is None:
        return {"status": "UNKNOWN", "reason": "cannot calculate narrative duration"}

    if actual_duration_minutes < min_duration_minutes:
        return {
            "status": "CONFLICT",
            "reason": f"actual duration {actual_duration_minutes} min < minimum required {min_duration_minutes} min",
            "min_required": min_duration_minutes,
            "actual": actual_duration_minutes,
        }

    return {"status": "OK", "duration": actual_duration_minutes, "min_required": min_duration_minutes}


def evaluate_shadow_coexistence(
    shadow_states: list[dict[str, Any]],
    canonical_states: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Check physical co-presence or location conflict between shadow and canonical character."""
    conflicts: list[dict[str, Any]] = []
    canonical_by_scene = {cs["scene_id"]: cs for cs in canonical_states if "scene_id" in cs}

    for ss in shadow_states:
        s_id = ss.get("scene_id")
        if s_id and s_id in canonical_by_scene:
            cs = canonical_by_scene[s_id]
            s_loc = ss.get("location")
            c_loc = cs.get("location")
            if s_loc and c_loc and s_loc != c_loc:
                conflicts.append({
                    "scene_id": s_id,
                    "type": "LOCATION_DISCREPANCY",
                    "shadow_location": s_loc,
                    "canonical_location": c_loc,
                })
    return conflicts


def check_character_knowledge_violation(
    character_id: int,
    known_secret_ids: set[int],
    scene_secret_mentions: list[int],
) -> list[int]:
    """Return list of secret IDs that are referenced in scene without character prior knowledge."""
    if not character_id or character_id <= 0:
        return []
    return [sec_id for sec_id in scene_secret_mentions if sec_id not in known_secret_ids]


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


def estimate_tokens(text: str) -> int:
    """Estimate token count based on character length heuristics."""
    if not text:
        return 0
    return max(1, len(text) // 2)

