from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    host: str = "127.0.0.1"
    port: int = 8000
    project_db_name: str = ".novelagent/project.db"

    def db_path(self, project_dir: Path) -> Path:
        return project_dir / self.project_db_name
