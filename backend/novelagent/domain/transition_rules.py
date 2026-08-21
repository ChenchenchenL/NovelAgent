from __future__ import annotations

from typing import Any, Optional


def check_trigger_condition(
    trigger_type: str | None,
    params: dict[str, Any] | None,
    context: dict[str, Any],
) -> bool:
    """Evaluate whether a foreshadowing trigger condition is met in context."""
    if not trigger_type or not params:
        return False

    if trigger_type == "CHARACTER_ARRIVES":
        target_char = params.get("character_id")
        target_loc = params.get("location_id") or params.get("location")
        curr_chars = context.get("characters_present", [])
        curr_loc = context.get("location_id") or context.get("location")
        if target_char in curr_chars and target_loc == curr_loc:
            return True

    elif trigger_type == "CHARACTER_OBTAINS":
        target_char = params.get("character_id")
        target_item = params.get("item_id")
        obtained = context.get("obtained_items", [])  # list of {character_id, item_id}
        if any(o.get("character_id") == target_char and o.get("item_id") == target_item for o in obtained):
            return True

    elif trigger_type == "CHARACTER_HEARS":
        target_char = params.get("character_id")
        keyword = str(params.get("keyword", "")).lower()
        curr_chars = context.get("characters_present", [])
        scene_text = str(context.get("text", "")).lower()
        if target_char in curr_chars and keyword and keyword in scene_text:
            return True

    elif trigger_type == "EVENT_OCCURS":
        target_event = params.get("event_type")
        target_entity = params.get("entity_id")
        events = context.get("events_occurred", [])  # list of {event_type, entity_id}
        if any(e.get("event_type") == target_event and (not target_entity or e.get("entity_id") == target_entity) for e in events):
            return True

    elif trigger_type == "RELATIONSHIP_REACHES":
        ca = params.get("character_a")
        cb = params.get("character_b")
        rel_type = params.get("type")
        relationships = context.get("relationships", [])  # list of {subject_id, object_id, type}
        if any(
            r.get("subject_id") == ca and r.get("object_id") == cb and r.get("type") == rel_type
            for r in relationships
        ):
            return True

    elif trigger_type == "TIME_ARRIVES":
        target_time = params.get("narrative_time")
        curr_time = context.get("narrative_time")
        if target_time and curr_time and target_time == curr_time:
            return True

    return False


def check_time_continuity(prev_exit: dict[str, Any], curr_entry: dict[str, Any]) -> dict[str, Any]:
    prev_time = prev_exit.get("narrative_time")
    curr_time = curr_entry.get("narrative_time")
    time_jump = curr_entry.get("time_jump")  # e.g., "3 days later"
    if prev_time and curr_time and prev_time > curr_time and not curr_entry.get("is_flashback"):
        return {"dimension": "TIME", "status": "CONFLICT", "message": f"叙事时间倒流：前场景={prev_time}, 当前={curr_time}"}
    if not time_jump and prev_time and curr_time and prev_time != curr_time:
        return {"dimension": "TIME", "status": "OK", "message": f"时间顺延: {prev_time} -> {curr_time}"}
    return {"dimension": "TIME", "status": "OK", "message": "时间过渡平稳"}


def check_location_continuity(prev_exit: dict[str, Any], curr_entry: dict[str, Any]) -> dict[str, Any]:
    prev_loc = prev_exit.get("location")
    curr_loc = curr_entry.get("location")
    if prev_loc and curr_loc and prev_loc != curr_loc:
        if not curr_entry.get("has_travel_transition") and not curr_entry.get("intentional_cut"):
            return {"dimension": "SPACE", "status": "WARNING", "message": f"跨地点切换未见明显位移说明：从 {prev_loc} 到 {curr_loc}"}
    return {"dimension": "SPACE", "status": "OK", "message": "地点过渡连续"}


def check_character_continuity(prev_exit: dict[str, Any], curr_entry: dict[str, Any]) -> dict[str, Any]:
    prev_injured = prev_exit.get("injured_characters", [])
    curr_recovered = curr_entry.get("healthy_characters", [])
    overlap = set(prev_injured).intersection(set(curr_recovered))
    if overlap:
        return {"dimension": "CHARACTER", "status": "CONFLICT", "message": f"重伤人物未作医治说明直接恢复：{list(overlap)}"}
    return {"dimension": "CHARACTER", "status": "OK", "message": "人物状态连续"}


def check_action_continuity(prev_exit: dict[str, Any], curr_entry: dict[str, Any]) -> dict[str, Any]:
    pending_action = prev_exit.get("pending_action")  # e.g., "sword_drawn", "combat"
    handled_action = curr_entry.get("resumed_action")
    if pending_action and not handled_action and not curr_entry.get("intentional_cut"):
        return {"dimension": "ACTION", "status": "WARNING", "message": f"前场景悬置动作未承接：{pending_action}"}
    return {"dimension": "ACTION", "status": "OK", "message": "行动逻辑连续"}


def check_emotion_continuity(prev_exit: dict[str, Any], curr_entry: dict[str, Any]) -> dict[str, Any]:
    prev_tension = prev_exit.get("emotional_tension", "NORMAL")  # HIGH, CRISIS, NORMAL
    curr_mood = curr_entry.get("mood", "NORMAL")
    if prev_tension == "CRISIS" and curr_mood == "RELAXED" and not curr_entry.get("intentional_cut"):
        return {"dimension": "EMOTION", "status": "WARNING", "message": "危机高潮情绪突变至极度松弛，缺少过渡铺垫"}
    return {"dimension": "EMOTION", "status": "OK", "message": "情绪张力自然"}


def check_information_continuity(prev_exit: dict[str, Any], curr_entry: dict[str, Any]) -> dict[str, Any]:
    leaked_secrets = curr_entry.get("disclosed_secrets", [])
    known_secrets = prev_exit.get("known_secrets", [])
    unauthorized = [s for s in leaked_secrets if s not in known_secrets]
    if unauthorized:
        return {"dimension": "INFORMATION", "status": "CONFLICT", "message": f"角色涉及未知核心信息泄露: {unauthorized}"}
    return {"dimension": "INFORMATION", "status": "OK", "message": "叙事信息边界清晰"}


def check_pov_continuity(prev_exit: dict[str, Any], curr_entry: dict[str, Any]) -> dict[str, Any]:
    prev_pov = prev_exit.get("pov")
    curr_pov = curr_entry.get("pov")
    if prev_pov and curr_pov and prev_pov != curr_pov:
        if not curr_entry.get("pov_shift_allowed", True):
            return {"dimension": "POV", "status": "CONFLICT", "message": f"POV 视角冲突切换：{prev_pov} -> {curr_pov}"}
    return {"dimension": "POV", "status": "OK", "message": "视角连贯"}


def evaluate_scene_transition(prev_exit: dict[str, Any] | None, curr_entry: dict[str, Any] | None) -> dict[str, Any]:
    """Inspect scene transition contract against exit state."""
    p_exit = prev_exit or {}
    c_entry = curr_entry or {}

    if c_entry.get("intentional_cut"):
        return {
            "status": "INTENTIONAL_CUT",
            "message": "作者标记为有意跳切（文学留白）",
            "checks": [],
        }

    checks = [
        check_time_continuity(p_exit, c_entry),
        check_location_continuity(p_exit, c_entry),
        check_character_continuity(p_exit, c_entry),
        check_action_continuity(p_exit, c_entry),
        check_emotion_continuity(p_exit, c_entry),
        check_information_continuity(p_exit, c_entry),
        check_pov_continuity(p_exit, c_entry),
    ]

    has_conflict = any(c.get("status") == "CONFLICT" for c in checks)
    has_warning = any(c.get("status") == "WARNING" for c in checks)

    status = "CONFLICT" if has_conflict else ("WARNING" if has_warning else "OK")
    return {
        "status": status,
        "checks": checks,
        "message": "存在硬冲突" if has_conflict else ("存在需关注的跳跃警告" if has_warning else "过渡平稳连续"),
    }


from .rules import estimate_tokens

