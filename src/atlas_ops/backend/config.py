from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import yaml
from pydantic import BaseModel, Field


class Site(BaseModel):
    name: str
    description: Optional[str] = None
    host: Optional[str] = None


class BackendSettings(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    db_url: str = "sqlite:////data/atlas_ops.db"
    shared_token: str = "changeme"
    allow_origins: List[str] = Field(default_factory=lambda: ["*"])
    sites: List[Site] = Field(default_factory=lambda: [
        Site(name="local-docker", description="Local Docker host", host="localhost"),
    ])


def load_backend_config(path: Path) -> BackendSettings:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return BackendSettings(**data)


def save_backend_config(path: Path, settings: BackendSettings) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(settings.model_dump_yaml(), encoding="utf-8")

