from __future__ import annotations

from typing import Any


def detect_logical_communities(
    volumes: list[dict[str, Any]],
    plot_threads: list[dict[str, Any]],
    factions: list[str] | None = None,
    custom_tags: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Detect logical communities from canonical hierarchy and plot structure."""
    communities: list[dict[str, Any]] = []

    # 1. Volume Communities
    for vol in volumes:
        v_id = vol.get("id")
        v_title = vol.get("title", f"第{v_id}卷")
        communities.append({
            "name": f"卷社区: {v_title}",
            "community_type": "VOLUME",
            "source_entity_type": "VOLUME",
            "source_entity_id": v_id,
            "tags": ["volume", f"vol_{v_id}"],
        })

    # 2. Plot Thread Communities
    for pt in plot_threads:
        pt_id = pt.get("id")
        pt_name = pt.get("name", f"剧情线#{pt_id}")
        communities.append({
            "name": f"剧情线社区: {pt_name}",
            "community_type": "PLOT_THREAD",
            "source_entity_type": "PLOT_THREAD",
            "source_entity_id": pt_id,
            "tags": ["plot_thread", f"pt_{pt_id}", str(pt.get("priority", "MAIN"))],
        })

    # 3. Faction Communities
    for fac in (factions or []):
        if fac.strip():
            communities.append({
                "name": f"阵营社区: {fac.strip()}",
                "community_type": "FACTION",
                "source_entity_type": "FACTION",
                "source_entity_id": None,
                "tags": ["faction", fac.strip()],
            })

    # 4. Custom Tag Communities
    for tag in (custom_tags or []):
        if tag.strip():
            communities.append({
                "name": f"自定义社区: {tag.strip()}",
                "community_type": "CUSTOM",
                "source_entity_type": "CUSTOM",
                "source_entity_id": None,
                "tags": ["custom", tag.strip()],
            })

    return communities


def analyze_character_arc(
    char_name: str,
    states: list[dict[str, Any]],
) -> dict[str, Any]:
    """Analyze character growth arc, stage transitions, and turning points."""
    sorted_states = sorted(states, key=lambda s: s.get("scene_id", 0))
    stages: list[dict[str, Any]] = []
    turning_points: list[dict[str, Any]] = []

    last_loc = None
    last_emotion = None
    last_arc_stage = None

    for st in sorted_states:
        s_id = st.get("scene_id")
        loc = st.get("location")
        emotion = st.get("emotion")
        arc_stage = st.get("arc_stage")

        if arc_stage and arc_stage != last_arc_stage:
            stages.append({
                "scene_id": s_id,
                "stage": arc_stage,
                "narrative_time": st.get("narrative_time"),
            })
            turning_points.append({
                "scene_id": s_id,
                "type": "ARC_STAGE_CHANGE",
                "from_stage": last_arc_stage,
                "to_stage": arc_stage,
                "description": f"人物阶段转变为 {arc_stage}",
            })
            last_arc_stage = arc_stage

        if emotion and emotion != last_emotion and last_emotion is not None:
            turning_points.append({
                "scene_id": s_id,
                "type": "EMOTIONAL_SHIFT",
                "from_emotion": last_emotion,
                "to_emotion": emotion,
                "description": f"情绪转变: {last_emotion} -> {emotion}",
            })
        last_emotion = emotion
        last_loc = loc

    return {
        "character_name": char_name,
        "total_states": len(sorted_states),
        "stages": stages,
        "turning_points": turning_points,
        "is_complete": len(stages) >= 2,
    }


def analyze_foreshadow_fulfillment(
    foreshadowings: list[dict[str, Any]],
    current_scene_index: int = 0,
) -> dict[str, Any]:
    """Calculate foreshadowing fulfillment rates, overdue risks, and unfulfilled list."""
    total = len(foreshadowings)
    if total == 0:
        return {
            "total": 0,
            "fulfilled": 0,
            "pending": 0,
            "abandoned": 0,
            "fulfillment_rate": 1.0,
            "overdue_items": [],
            "active_items": [],
        }

    fulfilled = [f for f in foreshadowings if f.get("status") in {"RESOLVED", "PAYOFF"}]
    pending = [f for f in foreshadowings if f.get("status") in {"SETUP", "DEVELOP", "PLANNED", "ACTIVE"}]
    abandoned = [f for f in foreshadowings if f.get("status") == "ABANDONED"]

    overdue_items = []
    for f in pending:
        max_ch = f.get("target_chapter_end") or f.get("target_chapter_max")
        if max_ch and current_scene_index > max_ch:
            overdue_items.append(f)

    rate = round(len(fulfilled) / max(1, (total - len(abandoned))), 2)
    return {
        "total": total,
        "fulfilled": len(fulfilled),
        "pending": len(pending),
        "abandoned": len(abandoned),
        "fulfillment_rate": rate,
        "overdue_items": overdue_items,
        "active_items": pending,
    }


def analyze_plot_ruptures(
    plot_threads: list[dict[str, Any]],
    events: list[dict[str, Any]],
    scene_count: int,
) -> list[dict[str, Any]]:
    """Detect broken or neglected narrative threads without recent progression."""
    ruptures: list[dict[str, Any]] = []
    events_by_thread: dict[int, list[dict[str, Any]]] = {}
    for ev in events:
        tid = ev.get("thread_id")
        if tid:
            events_by_thread.setdefault(tid, []).append(ev)

    for pt in plot_threads:
        tid = pt.get("id")
        t_status = pt.get("status")
        t_name = pt.get("name", f"线索#{tid}")
        t_events = events_by_thread.get(tid, [])

        if t_status == "ACTIVE" and len(t_events) == 0 and scene_count >= 5:
            ruptures.append({
                "thread_id": tid,
                "thread_name": t_name,
                "issue_type": "DORMANT_PLOT_THREAD",
                "severity": "WARNING",
                "description": f"剧情线【{t_name}】处于活跃状态但在全书无任何推进事件记录",
                "suggestion": "为该剧情线安排推进事件或调整为规划状态",
            })
        elif t_status == "ACTIVE" and t_events:
            max_scene = max(e.get("scene_id", 0) for e in t_events)
            if scene_count - max_scene >= 10:
                ruptures.append({
                    "thread_id": tid,
                    "thread_name": t_name,
                    "issue_type": "LONG_NEGLECTED_THREAD",
                    "severity": "WARNING",
                    "description": f"剧情线【{t_name}】已连续 {scene_count - max_scene} 个场景未出现进展",
                    "suggestion": "适时安排插曲回收或推进该线索",
                })
    return ruptures


def calculate_feedback_optimization_suggestions(
    feedback_stats: dict[str, Any],
) -> list[dict[str, Any]]:
    """Generate optimization suggestions based on author ignore/reject false positive rates."""
    suggestions: list[dict[str, Any]] = []
    by_type = feedback_stats.get("by_issue_type", {})

    for issue_type, counts in by_type.items():
        total = counts.get("total", 0)
        ignore_cnt = counts.get("ignore", 0)
        reject_cnt = counts.get("reject", 0)
        fp_rate = (ignore_cnt + reject_cnt) / max(1, total)

        if total >= 3 and fp_rate >= 0.5:
            suggestions.append({
                "issue_type": issue_type,
                "action": "SUPPRESS_OR_RELAX",
                "false_positive_rate": round(fp_rate, 2),
                "reason": f"{issue_type} 误报/忽略率达到 {round(fp_rate * 100)}% (共 {total} 次反馈)",
                "recommended_fix": f"降低 {issue_type} 的敏感度阈值或在对应场景默认放行",
            })
    return suggestions
