from __future__ import annotations

from pathlib import Path
from typing import List

import yaml
from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    backend_url: str = "http://localhost:8000"
    shared_token: str = "changeme"
    docker_hosts: List[str] = Field(default_factory=lambda: ["unix:///var/run/docker.sock"])
    poll_interval: int = 60


def load_agent_config(path: Path) -> AgentConfig:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return AgentConfig(**data)


def save_agent_config(path: Path, config: AgentConfig) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(config.model_dump_yaml(), encoding="utf-8")

