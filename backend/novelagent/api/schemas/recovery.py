from __future__ import annotations

from typing import Any, Literal, Optional
from pydantic import BaseModel


class FsckResolveConflictRequest(BaseModel):
    journal_id: int
    resolution: Literal["SQLITE", "FILE", "DUAL"]


class BackupRequest(BaseModel):
    output_path: Optional[str] = None


class BackupResponse(BaseModel):
    status: str = "ok"
    output_path: str


class ExportRequest(BaseModel):
    format: Literal["markdown", "json"] = "markdown"
    output_path: Optional[str] = None


class RestoreRequest(BaseModel):
    backup_file: str
