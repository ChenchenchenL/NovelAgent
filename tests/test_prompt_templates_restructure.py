import pytest
from novelagent.integrations.prompt_templates import (
    DEFAULT_TEMPLATES,
    SYSTEM_PROMPTS,
    TEMPLATE_SYSTEM_MAPPING,
    render_messages,
    render_prompt,
    render_text,
)


def test_system_prompt_personas_and_rules():
    """Verify Layer 0 System Prompt personas and core literary rules."""
    assert "default_novelist" in SYSTEM_PROMPTS
    assert "critic_editor" in SYSTEM_PROMPTS
    assert "knowledge_extractor" in SYSTEM_PROMPTS
    assert "director_planner" in SYSTEM_PROMPTS

    novelist_sys = SYSTEM_PROMPTS["default_novelist"]
    assert "Show, Don't Tell" in novelist_sys
    assert "动词驱动" in novelist_sys
    assert "严禁高频 AI 套话" in novelist_sys
    assert "深吸一口气" in novelist_sys
    assert "深层视点限制（Deep POV）" in novelist_sys


def test_render_prompt_backward_compatibility():
    """Verify render_prompt returns pure string user prompt for backward compatibility."""
    ctx = {
        "pov": "林舟",
        "location": "落云宗后山",
        "goal": "探寻古老石碑",
        "character_states": "状态良好",
        "context_text": "前情提要...",
        "recent_text": "寒风呼啸...",
        "instruction": "推开石门",
    }
    rendered = render_prompt("paragraph_generation", ctx)
    assert isinstance(rendered, str)
    assert "【场景视点】：林舟" in rendered
    assert "【发生地点】：落云宗后山" in rendered
    assert "推开石门" in rendered
    assert "{pov}" not in rendered
    assert "{location}" not in rendered


def test_render_messages_structure_and_personas():
    """Verify render_messages returns structured system and user message list."""
    ctx = {
        "pov": "林舟",
        "location": "破庙",
        "goal": "避雨",
        "character_states": "轻伤",
        "context_text": "大雨倾盆...",
        "recent_text": "雷声隆隆...",
        "instruction": "生火取暖",
    }
    messages = render_messages("paragraph_generation", ctx)
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert "顶级小说主创编剧" in messages[0]["content"]
    assert messages[1]["role"] == "user"
    assert "【场景视点】：林舟" in messages[1]["content"]


def test_refine_polish_template_rendering():
    """Verify Layer 2 refine_polish template renders critique issues and original draft."""
    ctx = {
        "cliche_issues": "夜色深沉 (高频套话), 空气中弥漫着危险 (平庸描写)",
        "critique_feedback": "缺少肢体微动作，情绪过于抽象讲述 (Tell)",
        "voice_drift": "无明显偏离",
        "original_draft": "夜色深沉，林舟感到十分愤怒。空气中弥漫着危险的气息。",
        "instruction": "强化环境冷雨感官与咬牙微动作，剔除AI套话",
    }
    messages = render_messages("refine_polish", ctx)
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert "极其严苛的资深文学主编" in messages[0]["content"]

    user_txt = messages[1]["content"]
    assert "【待修润原段落】" in user_txt
    assert "夜色深沉 (高频套话)" in user_txt
    assert "强化环境冷雨感官" in user_txt


def test_modality_inference_few_shot_examples():
    """Verify modality_inference prompt includes all 9 modalities and Few-Shot examples."""
    ctx = {
        "sentence": "听说后山封印着一条上古魔龙。",
        "context": "客栈中众人议论纷纷。",
    }
    messages = render_messages("modality_inference", ctx)
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert "文学事实与知识图谱抽取引擎" in messages[0]["content"]

    user_txt = messages[1]["content"]
    assert "ACTUAL" in user_txt
    assert "BELIEVED" in user_txt
    assert "REPORTED" in user_txt
    assert "METAPHORICAL" in user_txt
    assert "【Few-Shot 范例】" in user_txt
    assert "范例 1" in user_txt
    assert "【待分析句子】\n听说后山封印着一条上古魔龙。" in user_txt


def test_placeholder_safe_cleaning():
    """Verify unfilled placeholders are cleanly stripped by regex cleaner."""
    ctx = {
        "pov": "林舟",
        # location and goal are omitted
    }
    rendered = render_prompt("paragraph_generation", ctx)
    assert "【场景视点】：林舟" in rendered
    assert "{location}" not in rendered
    assert "{goal}" not in rendered
    assert "{" not in rendered and "}" not in rendered


def test_custom_template_and_custom_system_override():
    """Verify callers can override default templates or custom system prompts."""
    ctx = {"target": "暗门"}
    custom_sys = "你是一位暗黑克苏鲁小说家。"
    custom_tmpl = "请描写主角发现{target}时的惊悚san值狂掉感。"

    messages = render_messages(
        "paragraph_generation",
        ctx,
        custom_system=custom_sys,
        custom_template=custom_tmpl,
    )
    assert messages[0]["content"] == custom_sys
    assert messages[1]["content"] == "请描写主角发现暗门时的惊悚san值狂掉感。"
