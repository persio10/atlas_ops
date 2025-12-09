from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import BackendSettings
from .db import SignalStore
from .routes import get_settings, get_store, router


def create_app(settings: BackendSettings, store: SignalStore) -> FastAPI:
    app = FastAPI(title="Atlas Ops Backend", version="0.4.2")

    app.state.settings = settings
    app.state.store = store

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.dependency_overrides = {
        get_settings: lambda: settings,
        get_store: lambda: store,
    }

    app.include_router(router, dependencies=[])

    base_dir = Path(__file__).resolve().parent.parent
    frontend_dir = base_dir / "frontend"
    if frontend_dir.exists():
        app.mount("/frontend", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")

    return app


__all__ = ["create_app"]
