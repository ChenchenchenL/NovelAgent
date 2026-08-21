from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    instruction: str = "继续当前场景"
    tier: Literal["T1", "T2", "T3"] = "T2"


class ModelSettingsRequest(BaseModel):
    endpoint: str
    models: dict[str, str] = Field(default_factory=dict)
    api_key: Optional[str] = None


class GenerationRunCreate(BaseModel):
    task_type: Optional[str] = "paragraph_generation"
    prompt_template: Optional[str] = None
    instruction: Optional[str] = None
    tier: Optional[Literal["T1", "T2", "T3"]] = "T3"
    context_source_ids: Optional[list[str]] = None
    parameters: Optional[dict] = None
    target_range: Optional[dict] = None


class GenerationRunView(BaseModel):
    id: int
    scene_id: int
    task_type: str = "paragraph_generation"
    status: str = "CREATED"
    model_tier: str = "T3"
    actual_model: str = ""
    progress: Optional[float] = None
    token_usage: Optional[dict] = None
    error_message: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    created_at: str = ""
