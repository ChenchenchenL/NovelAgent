from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from ..dependencies import (
    AppState,
    get_app_state,
    native_select_directory,
    require_session,
)
from ..schemas import DirectorySelection, ModelSettingsRequest
from ...infrastructure.fsck import check_project
from ...integrations.model_gateway import ModelConfig, ModelGateway

router = APIRouter(tags=["System"])


@router.get("/api/health")
def health(state: AppState = Depends(get_app_state)) -> dict[str, Any]:
    return {"status": "ok", "project_open": state.project_dir is not None}


@router.get("/api/session")
def session(response: Response, state: AppState = Depends(get_app_state)) -> dict[str, str]:
    response.set_cookie("novelagent_session", state.session_token, httponly=True, samesite="strict")
    return {"token": state.session_token}


@router.get("/api/settings/model")
def get_model_settings(state: AppState = Depends(require_session)) -> dict[str, Any]:
    return {"endpoint": state.model_config.endpoint, "models": state.model_config.models}


@router.post("/api/settings/model")
def save_model_settings(payload: ModelSettingsRequest, state: AppState = Depends(require_session)) -> dict[str, Any]:
    models = payload.models or ModelConfig(endpoint=payload.endpoint).models
    state.model_config = ModelConfig(endpoint=payload.endpoint, models=models)
    if payload.api_key:
        try:
            ModelGateway.save_key("novelagent", payload.endpoint, payload.api_key)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"操作系统 Keyring 不可用：{exc}") from exc
    return {
        "endpoint": state.model_config.endpoint,
        "models": state.model_config.models,
        "key_saved": bool(payload.api_key),
    }


@router.post("/api/workspaces/select-directory")
def select_directory(selection: DirectorySelection | None = None, state: AppState = Depends(require_session)) -> dict[str, Any]:
    current = selection.current_path if selection else native_select_directory()
    if not current:
        raise HTTPException(status_code=501, detail="当前环境无法打开原生目录选择器，请通过 API 提供路径")
    current_path = Path(current).expanduser().resolve()
    if not current_path.is_dir():
        raise HTTPException(status_code=400, detail="创作目录不存在")
    state.authorized_dirs.add(current_path)
    histories: list[str] = []
    if selection:
        for raw in selection.history_paths:
            path = Path(raw).expanduser().resolve()
            if path.is_dir():
                state.history_dirs.add(path)
                histories.append(str(path))
    return {"current_path": str(current_path), "history_paths": histories}


@router.post("/api/workspaces/select-history")
def select_history(state: AppState = Depends(require_session)) -> dict[str, Any]:
    selected = native_select_directory()
    if not selected:
        raise HTTPException(status_code=501, detail="当前环境无法打开原生目录选择器，请通过当前目录接口提供路径")
    path = Path(selected).expanduser().resolve()
    if not path.is_dir():
        raise HTTPException(status_code=400, detail="历史目录不存在")
    state.history_dirs.add(path)
    return {"path": str(path), "history_paths": [str(item) for item in sorted(state.history_dirs)]}


@router.post("/api/fsck")
def run_fsck(state: AppState = Depends(require_session)) -> dict[str, Any]:
    project_dir, factory = state.require_project()
    with factory() as session:
        return check_project(project_dir, session)
