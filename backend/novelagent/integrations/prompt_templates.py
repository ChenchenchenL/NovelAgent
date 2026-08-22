from __future__ import annotations

import re
from typing import Any

SYSTEM_PROMPTS: dict[str, str] = {
    "default_novelist": (
        "你是一位顶级小说主创编剧与文学作家。你的创作必须严格遵守以下文学铁律：\n"
        "1. 【Show, Don't Tell（呈现而非告知）】：严禁直接陈述角色抽象情绪（如'他很愤怒'），必须通过生理微反应（瞳孔骤缩、指节发白、呼吸停滞）、微观动作与环境质感来呈现；\n"
        "2. 【动词驱动与短句节奏】：以具体、强烈的动作动词推进叙事，减少冗余的'的/地/得'与连词（'随着'、'然而'、'在...之后'）。紧张场景多用短句；\n"
        "3. 【严禁高频 AI 套话（Negative Cliche Pool）】：严禁出现'深吸一口气'、'眼中闪过一丝复杂'、'空气中弥漫着...气息'、'这一刻'、'不得不说'、'嘴角勾起弧度'；\n"
        "4. 【深层视点限制（Deep POV）】：感知必须严格受限于视角人物（POV），不得以上帝视角描写视角人物看不见、听不到的背后细节。"
    ),
    "critic_editor": (
        "你是一位极其严苛的资深文学主编。你专注于挑出正文中的 AI 套话、抽象说教（Tell 句式）、肢体动作冲突、音色漂移与节奏平淡问题，并进行精准修润。"
    ),
    "knowledge_extractor": (
        "你是一个严谨的文学事实与知识图谱抽取引擎。你擅长从文学叙事中区分真实物理事实（ACTUAL）、角色主观信念（BELIEVED）、传言谣言（REPORTED）、回忆（REMEMBERED）、梦境（DREAMED）、假设（HYPOTHETICAL）与隐喻修辞（METAPHORICAL）。"
    ),
    "director_planner": (
        "你是一位宏观故事架构师与编剧导演。你擅长将创意种子拆解为引人入胜的世界观、立体的人物弧光、充满戏剧阻力的节拍契约与分卷大纲。"
    ),
}

DEFAULT_TEMPLATES: dict[str, str] = {
    "paragraph_generation": (
        "【场景视点】：{pov} | 【发生地点】：{location}\n"
        "【当前节拍目标】：{goal}（本段必须推进的核心动作或信息）\n"
        "【登场角色状态】：{character_states}\n\n"
        "【前情与背景设定】：\n"
        "{context_text}\n\n"
        "【当前正文末尾衔接】：\n"
        "{recent_text}\n\n"
        "【续写指令】：\n"
        "{instruction}\n\n"
        "【行文与感官要求】：\n"
        "- 融入至少 1 处环境质感（光影/气味/温度）与 1 处肢体生理微反应；\n"
        "- 紧接上文动作，直接输出小说正文："
    ),
    "refine_polish": (
        "请根据以下【质检缺陷报告】，针对【待修润原段落】进行定向精修润色，消除 AI 味并增强文学质感：\n\n"
        "【质检缺陷报告】：\n"
        "- 套话命中：{cliche_issues}\n"
        "- 逻辑与平淡问题：{critique_feedback}\n"
        "- 音色偏离：{voice_drift}\n\n"
        "【待修润原段落】：\n"
        "{original_draft}\n\n"
        "【修润指令】：\n"
        "{instruction}\n\n"
        "【修润要求】：\n"
        "1. 彻底剔除上述套话与平庸转折，将抽象情绪陈述改写为具体的肢体微反应与感官呈现；\n"
        "2. 保持与前后文的无缝衔接，直接输出润色后的替换正文："
    ),
    "modality_inference": (
        "请分析以下句子中事实陈述的模态类别：\n\n"
        "【模态定义】\n"
        "- ACTUAL: 故事世界中真实发生（如：林舟拔出腰间短剑）\n"
        "- BELIEVED: 角色主观相信但未被证实（如：他坚信师兄是被冤枉的）\n"
        "- REPORTED: 传闻、转述或谣言（如：听说后山封印着上古凶兽）\n"
        "- REMEMBERED: 回忆往事（如：他依稀想起三年前那个雨夜）\n"
        "- DREAMED: 梦境、幻象或幻觉（如：恍惚中他梦见自己化作了飞鸟）\n"
        "- HYPOTHETICAL: 假设、推测或条件句（如：若明夜动手，胜算只有三成）\n"
        "- COUNTERFACTUAL: 反事实（如：要是当初没有离开宗门，或许就不会发生惨剧）\n"
        "- METAPHORICAL: 隐喻、夸张或比喻（如：胸中怒火如同翻江倒海）\n"
        "- AMBIGUOUS: 存疑待定\n\n"
        "【Few-Shot 范例】\n"
        "范例 1：\n"
        "句子：掌柜压低声音说道：“据传那古墓深处藏有一枚万载玄冰魄。”\n"
        "输出：{{\"modality\": \"REPORTED\", \"confidence\": 0.95, \"reasoning\": \"带有'据传'转述标志词，属于传闻。\"}}\n\n"
        "范例 2：\n"
        "句子：林舟指尖扣住暗扣，一步步踏入幽暗的石室。\n"
        "输出：{{\"modality\": \"ACTUAL\", \"confidence\": 0.98, \"reasoning\": \"客观物理动作陈述，无虚拟或推测修饰。\"}}\n\n"
        "范例 3：\n"
        "句子：他感到胸口仿佛被千斤巨石压得喘不过气来。\n"
        "输出：{{\"modality\": \"METAPHORICAL\", \"confidence\": 0.92, \"reasoning\": \"'仿佛被千斤巨石压'属于心理感受的夸张比喻。\"}}\n\n"
        "【待分析句子】\n{sentence}\n"
        "【上下文参考】\n{context}\n\n"
        "【要求】只返回 JSON：{{\"modality\": \"...\", \"confidence\": 0.xx, \"reasoning\": \"...\"}}"
    ),
    "beat_plan": (
        "基于以下场景设定规划本场的剧情推进节拍（Beats）：\n"
        "视角：{pov} | 地点：{location}\n"
        "出场契约目标：{goal}\n"
        "核心戏剧冲突：{conflict}\n\n"
        "请拆解输出 3-5 个具体的剧情推进节拍，每个节拍必须包含：\n"
        "1. 触发事件与行动；\n"
        "2. 遭遇的阻力或转折；\n"
        "3. 产生的新信息或状态变化。"
    ),
    "novel_auto_plan": (
        "基于以下创意种子进行小说全局架构推演：\n"
        "【创意种子】：{seed_prompt}\n"
        "【目标题材】：{genre}\n"
        "【规划规模】：{target_volumes} 卷\n\n"
        "请推演输出：\n"
        "1. 世界观法则与核心冲突；\n"
        "2. 主角、反派与关键配角设定（姓名、性格、初始动机）；\n"
        "3. 主线剧情线与核心伏笔设计；\n"
        "4. 各卷核心主题与高潮节点。"
    ),
    "continuity_check": (
        "请检查以下正文草稿是否存在前后矛盾或逻辑冲突：\n\n"
        "【场景基础设定】：\n{scene_info}\n\n"
        "【已确认正典事实（Ground Truth）】：\n{canon_facts}\n\n"
        "【待审查正文草稿】：\n{draft_content}\n\n"
        "审查维度：人物位置、持有道具转移、身体伤势、已获知秘密越界、空间耗时矛盾。\n"
        "若发现冲突请逐项列出具体依据，若无冲突请明确回答“无冲突”。"
    ),
    "director_intent": (
        "请分析导演（人类作者）的自然语言指令意图：\n\n"
        "【指令内容】：{instruction}\n\n"
        "可选意图类别：\n"
        "- SUGGEST_OUTLINE: 大纲构思、卷章架构调整、剧情推演\n"
        "- TRIGGER_WRITING: 正文创作、场景续写、段落扩写\n"
        "- QUERY_GRAPH: 设定查询、人物关系检索、世界观回顾\n"
        "- GENERAL_ASSIST: 闲聊、创意思考、写作建议\n\n"
        "请返回 JSON：{{\"intent\": \"...\", \"confidence\": 0.xx, \"summary\": \"...\"}}"
    ),
    "scene_summary": (
        "请对以下小说场景正文进行客观事实摘要：\n\n"
        "{content}\n\n"
        "摘要要求：\n"
        "1. 提取核心情节推进、人物关键决策与状态改变；\n"
        "2. 过滤主观文学修辞，保持客观精炼，100-300字。"
    ),
}

TEMPLATE_SYSTEM_MAPPING: dict[str, str] = {
    "paragraph_generation": "default_novelist",
    "refine_polish": "critic_editor",
    "modality_inference": "knowledge_extractor",
    "beat_plan": "director_planner",
    "novel_auto_plan": "director_planner",
    "continuity_check": "critic_editor",
    "director_intent": "director_planner",
    "scene_summary": "knowledge_extractor",
}


def render_text(template_str: str, context: dict[str, Any]) -> str:
    """Safely substitute context variables and clean unpopulated placeholders."""
    result = template_str
    for key, value in context.items():
        placeholder = "{" + key + "}"
        result = result.replace(placeholder, str(value or ""))
    # Clean up any remaining unresolved {key} placeholders
    result = re.sub(r"\{[a-zA-Z0-9_]+\}", "", result)
    return result.strip()


def render_prompt(template_name: str, context: dict[str, Any], custom_template: str | None = None) -> str:
    """Render single text prompt for backward compatibility."""
    template = custom_template or DEFAULT_TEMPLATES.get(template_name, "{instruction}")
    return render_text(template, context)


def render_messages(
    template_name: str,
    context: dict[str, Any],
    custom_system: str | None = None,
    custom_template: str | None = None,
) -> list[dict[str, str]]:
    """Render structured messages with separated system persona and user prompt."""
    system_key = TEMPLATE_SYSTEM_MAPPING.get(template_name, "default_novelist")
    system_content = custom_system or SYSTEM_PROMPTS.get(system_key, SYSTEM_PROMPTS["default_novelist"])

    user_content = render_prompt(template_name, context, custom_template=custom_template)

    return [
        {"role": "system", "content": system_content.strip()},
        {"role": "user", "content": user_content.strip()},
    ]
