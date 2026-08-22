from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


class AgentAutoPlanRequest(BaseModel):
    seed_prompt: str = Field(..., min_length=2, description="小说核心创意、题材设定或初始故事梗概")
    genre: str = Field("仙侠修真", description="小说题材分类")
    target_volumes: int = Field(2, ge=1, le=5, description="规划总卷数")
    chapters_per_vol: int = Field(3, ge=1, le=10, description="每卷预设章节数")


class AgentAutoPlanResponse(BaseModel):
    project_id: int
    seed_prompt: str
    genre: str
    characters_created: list[str]
    plot_threads_created: list[str]
    volumes: list[dict[str, Any]]
    total_scenes: int
    communities_count: int


class AgentAutoWriteRequest(BaseModel):
    scene_id: int = Field(..., description="目标创作场景 ID")
    guidance: Optional[str] = Field(None, description="作者导演指导意见")
    target_word_count: int = Field(1200, ge=300, le=5000)
    auto_extract: bool = Field(True, description="是否自动提取新事实进化图谱与状态机")


class AgentAutoWriteResponse(BaseModel):
    scene_id: int
    scene_title: str
    revision_id: int
    content: str
    thought_process: dict[str, Any]


class AgentAutoAdvanceRequest(BaseModel):
    guidance: Optional[str] = Field(None, description="作者全局连载推进指导")


class AgentDirectorChatRequest(BaseModel):
    instruction: str = Field(..., min_length=1, description="作者给 AI 导演/主创团队的对话指令")
    current_scene_id: Optional[int] = None


class AgentDirectorChatResponse(BaseModel):
    project_id: int
    action: str
    reply: str
    current_scene_id: Optional[int] = None
