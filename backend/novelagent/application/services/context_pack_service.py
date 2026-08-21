from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Any, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...domain.continuity_models import (
    CharacterState,
    NarrativeSecret,
    RelationshipState,
    TravelProfile,
)
from ...domain.models import Chapter, ItemEntity, Project, Scene, SceneRevision
from ...domain.plot_models import Foreshadowing, PlotThread
from ...domain.transition_rules import estimate_tokens
from .kg_service import find_relationship_path
from .summary_service import hierarchical_retrieve


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def assemble_context_pack(
    session: Session,
    project_id: int,
    scene_id: int,
    instruction: str | None = None,
    selection: str | None = None,
    max_tokens: int = 8000,
    include_kg_paths: bool = False,
    include_community_summaries: bool = False,
) -> dict[str, Any]:
    scene = session.get(Scene, scene_id)
    if not scene:
        raise KeyError(f"场景不存在: ID {scene_id}")
    chapter = session.get(Chapter, scene.chapter_id)
    if not chapter or chapter.project_id != project_id:
        raise KeyError(f"场景不属于当前项目: ID {scene_id}")

    fragments: list[dict[str, Any]] = []
    used_tokens = 0

    # 1. Author instruction & selection (Priority 1)
    if instruction:
        cost = estimate_tokens(instruction)
        fragments.append({
            "fragment_type": "AUTHOR_INSTRUCTION",
            "content": instruction,
            "source_id": scene_id,
            "source_version": scene.current_revision_id or 1,
            "narrative_time": None,
            "modality": "ACTUAL",
            "confirmed": True,
            "relevance": 1.0,
            "truncatable": False,
            "tokens": cost,
        })
        used_tokens += cost

    if selection:
        cost = estimate_tokens(selection)
        fragments.append({
            "fragment_type": "USER_SELECTION",
            "content": selection,
            "source_id": scene_id,
            "source_version": scene.current_revision_id or 1,
            "narrative_time": None,
            "modality": "ACTUAL",
            "confirmed": True,
            "relevance": 1.0,
            "truncatable": False,
            "tokens": cost,
        })
        used_tokens += cost

    # 2. Scene Entry Contract & Recent text (Priority 2)
    if scene.entry_contract:
        txt = json.dumps(scene.entry_contract, ensure_ascii=False)
        cost = estimate_tokens(txt)
        fragments.append({
            "fragment_type": "SCENE_ENTRY_CONTRACT",
            "content": txt,
            "source_id": scene.id,
            "source_version": scene.current_revision_id or 1,
            "narrative_time": scene.entry_contract.get("narrative_time"),
            "modality": "ACTUAL",
            "confirmed": True,
            "relevance": 1.0,
            "truncatable": False,
            "tokens": cost,
        })
        used_tokens += cost

    # 3. Active Characters, Secrets, Relationships, Items (Priority 3)
    char_states = session.scalars(select(CharacterState).where(CharacterState.scene_id == scene_id)).all()
    for cs in char_states:
        txt = f"角色#{cs.character_id} 状态: 位置={cs.location or '未知'}, 状态={cs.physical_state or '正常'}, 情绪={cs.emotion or '平稳'}"
        cost = estimate_tokens(txt)
        if used_tokens + cost <= max_tokens:
            fragments.append({
                "fragment_type": "CHARACTER_STATE",
                "content": txt,
                "source_id": cs.id,
                "source_version": 1,
                "narrative_time": cs.narrative_time,
                "modality": "ACTUAL",
                "confirmed": cs.confirmed,
                "relevance": 0.9,
                "truncatable": True,
                "tokens": cost,
            })
            used_tokens += cost

    # 4. Active Plot Threads & Foreshadowings (Priority 4)
    threads = session.scalars(
        select(PlotThread).where(PlotThread.project_id == project_id, PlotThread.status == "ACTIVE")
    ).all()
    for t in threads:
        txt = f"活跃剧情线: {t.name} (优先级 {t.priority}) - {t.description or ''}"
        cost = estimate_tokens(txt)
        if used_tokens + cost <= max_tokens:
            fragments.append({
                "fragment_type": "PLOT_THREAD",
                "content": txt,
                "source_id": t.id,
                "source_version": 1,
                "modality": "ACTUAL",
                "confirmed": True,
                "relevance": 0.85,
                "truncatable": True,
                "tokens": cost,
            })
            used_tokens += cost

    # 5. Travel profiles (Priority 5)
    profiles = session.scalars(select(TravelProfile).where(TravelProfile.project_id == project_id)).all()
    for tp in profiles:
        txt = f"空间移动规则: 从 {tp.from_location_id} 到 {tp.to_location_id}, 方式={tp.method}, 耗时={tp.duration_minutes}分钟"
        cost = estimate_tokens(txt)
        if used_tokens + cost <= max_tokens:
            fragments.append({
                "fragment_type": "TRAVEL_PROFILE",
                "content": txt,
                "source_id": tp.id,
                "source_version": 1,
                "modality": "ACTUAL",
                "confirmed": True,
                "relevance": 0.7,
                "truncatable": True,
                "tokens": cost,
            })
            used_tokens += cost

    # 6. H-RAG Recall (Priority 6)
    if used_tokens < max_tokens:
        hrag_frags = hierarchical_retrieve(session, project_id, scene_id, max_tokens=max_tokens - used_tokens)
        for hf in hrag_frags:
            fragments.append({
                "fragment_type": hf["type"],
                "content": hf["content"],
                "source_id": hf["source_id"],
                "source_version": hf["version"],
                "modality": "ACTUAL",
                "confirmed": True,
                "relevance": 0.8,
                "truncatable": True,
                "tokens": hf["tokens"],
            })
            used_tokens += hf["tokens"]

    return {
        "project_id": project_id,
        "scene_id": scene_id,
        "fragments": fragments,
        "total_tokens": used_tokens,
        "assembled_at": _now(),
    }


def validate_context_pack(pack_data: dict[str, Any]) -> dict[str, Any]:
    issues = []
    fragments = pack_data.get("fragments", [])
    for idx, f in enumerate(fragments):
        if not f.get("source_id"):
            issues.append(f"片段 #{idx} 缺失 source_id")
        if not f.get("source_version"):
            issues.append(f"片段 #{idx} 缺失 source_version")
        if not f.get("modality"):
            issues.append(f"片段 #{idx} 缺失 modality")
    return {
        "valid": len(issues) == 0,
        "fragment_count": len(fragments),
        "total_tokens": pack_data.get("total_tokens", 0),
        "issues": issues,
    }
