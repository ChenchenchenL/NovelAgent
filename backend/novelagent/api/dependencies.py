from __future__ import annotations

import secrets
import threading
from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import HTTPException, Request

from ..config.settings import Settings
from ..infrastructure.security import hash_text, is_path_allowed
from ..integrations.model_gateway import ModelConfig

if TYPE_CHECKING:
    from sqlalchemy.orm import Session, sessionmaker
    from ..domain.models import Scene


class AppState:
    """Application-level runtime state."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.session_token = secrets.token_urlsafe(24)
        self.authorized_dirs: set[Path] = set()
        self.history_dirs: set[Path] = set()
        self.project_dir: Path | None = None
        self.engine = None
        self.session_factory: sessionmaker | None = None
        self.events: dict[int, list[dict[str, str]]] = {}
        self.event_lock = threading.Lock()
        self.model_config = ModelConfig(endpoint="")

    def require_project(self) -> tuple[Path, sessionmaker]:
        if not self.project_dir or not self.session_factory:
            raise HTTPException(status_code=409, detail="请先选择并打开创作目录")
        return self.project_dir, self.session_factory


def get_app_state(request: Request) -> AppState:
    return request.app.state.novelagent


def require_session(request: Request) -> AppState:
    state = get_app_state(request)
    token = request.headers.get("X-NovelAgent-Token") or request.cookies.get("novelagent_session")
    if token != state.session_token:
        raise HTTPException(status_code=401, detail="本机会话令牌无效")
    return state


def native_select_directory() -> str | None:
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        selected = filedialog.askdirectory(title="选择 NovelAgent 创作目录")
        root.destroy()
        return selected or None
    except Exception:
        return None


def get_scene_content(session: Session, scene: Scene) -> str:
    from ..domain.models import SceneRevision

    if not scene.current_revision_id:
        return ""
    revision = session.get(SceneRevision, scene.current_revision_id)
    return revision.content if revision else ""


def append_event(state: AppState, run_id: int, kind: str, payload: str) -> None:
    with state.event_lock:
        state.events.setdefault(run_id, []).append({"event": kind, "data": payload})


__all__ = [
    "AppState",
    "append_event",
    "get_app_state",
    "get_scene_content",
    "hash_text",
    "is_path_allowed",
    "native_select_directory",
    "require_session",
]
