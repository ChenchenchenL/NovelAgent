from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


class ImportJobCreate(BaseModel):
    source_path: str
    batch_size: int = Field(10, ge=1, le=100)
    auto_extract: bool = False


class ImportJobView(BaseModel):
    id: int
    project_id: int
    source_path: str
    status: str = "PENDING"
    checkpoint: int = 0
    total_files: int = 0
    total_batches: int = 0
    batch_size: int = 10
    auto_extract: bool = False
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    created_at: Optional[str] = None
    error_summary: Optional[str] = None


class ImportCheckpointView(BaseModel):
    id: int
    job_id: int
    batch_index: int
    file_path: Optional[str] = None
    batch_info: Optional[dict[str, Any]] = None
    items_imported: int = 0
    status: str = "PENDING"
    error_message: Optional[str] = None
    created_at: Optional[str] = None


class ImportJobCreateResponse(BaseModel):
    id: int
    job_id: int
    status: str
    total_files: int
    total_batches: int
    sse_url: str
