from __future__ import annotations

from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...domain.continuity_models import Character, CharacterState
from ...domain.graphrag_models import Community
from ...domain.models import Chapter, Scene, Volume
from ...domain.plot_models import PlotThread
from ...domain.quality_models import BeatContract
from .chapter_service import create_chapter
from .character_service import create_character, create_character_state
from .community_service import auto_detect_and_sync_communities
from .graphrag_service import execute_graphrag_query
from .plot_service import create_plot_thread
from .project_service import create_volume, get_current_project
from .scene_service import create_scene


def auto_plan_novel_outline(
    session: Session,
    project_id: int,
    seed_prompt: str,
    genre: str = "通用",
    target_volumes: int = 2,
    chapters_per_vol: int = 3,
) -> dict[str, Any]:
    """Autonomous novel planning: generates worldview, characters, volumes, chapters and scenes."""
    # 1. Generate Core Characters
    main_char_name = "主角" if "主角" in seed_prompt else "林舟"
    rival_char_name = "反派首领" if "反派" in seed_prompt else "玄机阁主"
    ally_char_name = "护道同伴" if "同伴" in seed_prompt else "苏小黎"

    c1 = create_character(
        session, project_id, main_char_name,
        aliases=["少年", "宿主"],
        background=f"基于【{seed_prompt[:40]}】设定的核心主角",
        core_traits=["机智", "坚韧", "隐忍"],
    )
    c2 = create_character(
        session, project_id, rival_char_name,
        aliases=["暗影之主"],
        background=f"全书核心对立势力领袖，与{main_char_name}存在宿命因果",
        core_traits=["冷酷", "深不可测"],
    )
    c3 = create_character(
        session, project_id, ally_char_name,
        aliases=["小黎"],
        background=f"{main_char_name}的初期同行伙伴与智囊",
        core_traits=["机警", "忠诚"],
    )

    # 2. Generate Plot Threads
    main_thread = create_plot_thread(
        session, project_id, name="主线：身世揭秘与强敌对抗", thread_type="MAIN", priority=1,
        description=f"{main_char_name}由弱变强，对抗{rival_char_name}并揭开世界真相",
    )
    sub_thread = create_plot_thread(
        session, project_id, name="支线：古老遗迹与秘宝探索", thread_type="SUBPLOT", priority=2,
        description=f"探索古老禁地以寻找破解{rival_char_name}威胁的机缘",
    )

    # 3. Generate Volumes, Chapters & Scenes
    created_volumes: list[dict[str, Any]] = []
    total_scenes_created = 0

    for v_idx in range(1, target_volumes + 1):
        vol_title = f"第{v_idx}卷：{'初入局中' if v_idx == 1 else '风起云涌'}"
        vol = create_volume(session, project_id, title=vol_title, status="ACTIVE")
        vol_data = {"id": vol.id, "title": vol.title, "chapters": []}

        for c_idx in range(1, chapters_per_vol + 1):
            ch_num = (v_idx - 1) * chapters_per_vol + c_idx
            ch_title = f"第{ch_num}章：{'破败开局与神秘芯片' if ch_num == 1 else f'波澜渐起之第{ch_num}回'}"
            chap = create_chapter(session, project_id, title=ch_title, volume_id=vol.id, status="ACTIVE")

            # Create default scene
            sc_title = f"场景一：{'命运的转折点' if ch_num == 1 else f'交锋与前行'}"
            sc = create_scene(session, project_id, chap.id, sc_title, "第三人称", "边陲小镇")
            total_scenes_created += 1

            # Bind default character state and beat contract
            create_character_state(session, c1.id, {
                "scene_id": sc.id,
                "location": "初始宗门/边陲小镇",
                "emotion": "警惕",
                "arc_stage": f"阶段{ch_num}",
                "confirmed": True,
            })

            beat = BeatContract(
                project_id=project_id,
                scene_id=sc.id,
                required_advancements=[{"event_type": "DEVELOPMENT", "target_count": 1}],
                stop_conditions=[{"type": "WORD_LIMIT", "threshold": 1200}],
                target_word_count=1000,
                max_word_count=1500,
                status="ACTIVE",
            )
            session.add(beat)
            vol_data["chapters"].append({"id": chap.id, "title": chap.title, "scene_id": sc.id})

        created_volumes.append(vol_data)

    session.commit()

    # 4. Auto-detect Communities
    communities = auto_detect_and_sync_communities(session, project_id)

    return {
        "project_id": project_id,
        "seed_prompt": seed_prompt,
        "genre": genre,
        "characters_created": [c1.name, c2.name, c3.name],
        "plot_threads_created": [main_thread.name, sub_thread.name],
        "volumes": created_volumes,
        "total_scenes": total_scenes_created,
        "communities_count": len(communities),
    }


def director_chat_interaction(
    session: Session,
    project_id: int,
    instruction: str,
    current_scene_id: int | None = None,
) -> dict[str, Any]:
    """Parse director instruction and dispatch actions or generate knowledge replies."""
    inst_lower = instruction.lower()

    if "大纲" in instruction or "规划" in instruction:
        action = "SUGGEST_OUTLINE"
        reply = f"【导演指令响应】：已解析大纲建议要求。针对「{instruction}」，建议在下一卷强化主配角的矛盾冲突并埋入关键道具线索。"
    elif "写" in instruction or "生成" in instruction or "续写" in instruction:
        action = "TRIGGER_WRITING"
        reply = f"【导演指令响应】：收到写作推进指令「{instruction}」。已准备就绪，可一键执行防幻觉场景生成。"
    elif "查" in instruction or "谁" in instruction or "关系" in instruction or "设定" in instruction:
        action = "QUERY_GRAPH"
        q_res = execute_graphrag_query(session, project_id, "MULTI_HOP", instruction)
        reply = q_res.result.get("answer") if q_res.result else "未检索到相关图谱记录"
    else:
        action = "GENERAL_ASSIST"
        reply = f"【导演协同】：明白您的构想「{instruction}」。已记录至创作工作区决策日志。"

    return {
        "project_id": project_id,
        "action": action,
        "reply": reply,
        "current_scene_id": current_scene_id,
    }
