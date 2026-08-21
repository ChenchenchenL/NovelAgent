from __future__ import annotations

import re
from typing import Any

DEFAULT_TEMPLATES: dict[str, str] = {
    "paragraph_generation": (
        "【场景背景】\n"
        "视角人物：{pov}\n"
        "发生地点：{location}\n"
        "场景目标：{goal}\n\n"
        "【前情与上下文】\n"
        "{context_text}\n\n"
        "【当前正文末尾】\n"
        "{recent_text}\n\n"
        "【续写指令】\n"
        "{instruction}\n\n"
        "请紧接上一段落继续创作，保持文风、语调与人物性格一致，不要重复已有文字，直接输出小说正文："
    ),
    "scene_summary": (
        "请对以下小说场景正文进行客观摘要，总结核心情节、人物行动与状态变化：\n\n"
        "{content}\n\n"
        "摘要要求：简洁准确，100-300字。"
    ),
    "beat_plan": (
        "基于以下场景设定规划本场的剧情节拍（Beats）：\n"
        "视角：{pov}，地点：{location}\n"
        "出场契约目标：{goal}\n"
        "设定冲突：{conflict}\n\n"
        "请输出 3-5 个具体的剧情推进节拍。"
    ),
    "continuity_check": (
        "请检查以下正文草稿是否存在前后矛盾或逻辑冲突：\n"
        "场景设定：{scene_info}\n"
        "已确认事实：{canon_facts}\n"
        "待检正文：\n{draft_content}\n\n"
        "若有冲突请列出，若无冲突请回答无。"
    ),
    "modality_inference": (
        "你是一个文学分析助手。请分析以下句子中事实陈述的模态类别：\n\n"
        "【句子】\n{sentence}\n\n"
        "【上下文】\n{context}\n\n"
        "【模态定义】\n"
        "- ACTUAL: 真实发生\n"
        "- BELIEVED: 角色主观相信\n"
        "- REPORTED: 传言转述\n"
        "- REMEMBERED: 回忆\n"
        "- DREAMED: 梦境幻觉\n"
        "- HYPOTHETICAL: 假设推断\n"
        "- COUNTERFACTUAL: 反事实\n"
        "- METAPHORICAL: 隐喻比喻\n"
        "- AMBIGUOUS: 存疑待定\n\n"
        "【要求】只返回 JSON：{{\"modality\": \"...\", \"confidence\": 0.xx, \"reasoning\": \"...\"}}"
    ),
}


def render_prompt(template_name: str, context: dict[str, Any], custom_template: str | None = None) -> str:
    template = custom_template or DEFAULT_TEMPLATES.get(template_name, "{instruction}")
    result = template
    for key, value in context.items():
        placeholder = "{" + key + "}"
        result = result.replace(placeholder, str(value or ""))
    # Clean up any unresolved {key}
    result = re.sub(r"\{[a-zA-Z0-9_]+\}", "", result)
    return result.strip()
