from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .dependencies import AppState
from .routers import (
    chapters,
    characters,
    claims,
    foreshadowings,
    generation,
    impact,
    imports,
    items,
    locations,
    patches,
    plots,
    projects,
    relationships,
    scenes,
    secrets,
    shadows,
    system,
    transitions,
    workspaces,
)
from ..config import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the NovelAgent FastAPI application."""
    state = AppState(settings)
    app = FastAPI(title="NovelAgent", version="0.1.0")
    app.state.novelagent = state

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register modular routers
    app.include_router(system.router)
    app.include_router(projects.router)
    app.include_router(chapters.router)
    app.include_router(scenes.router)
    app.include_router(characters.router)
    app.include_router(relationships.router)
    app.include_router(secrets.router)
    app.include_router(items.router)
    app.include_router(shadows.router)
    app.include_router(locations.router)
    app.include_router(plots.router)
    app.include_router(foreshadowings.router)
    app.include_router(transitions.router)
    app.include_router(impact.router)
    app.include_router(workspaces.router)
    app.include_router(patches.router)
    app.include_router(claims.router)
    app.include_router(generation.router)
    app.include_router(imports.router)

    # Static assets mounting for frontend production build
    dist_dir = Path(__file__).parent.parent.parent.parent / "frontend" / "dist"
    if dist_dir.is_dir():
        app.mount("/", StaticFiles(directory=dist_dir, html=True), name="static")

    return app


__all__ = ["AppState", "create_app"]
