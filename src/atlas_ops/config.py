from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import yaml

DEFAULT_CONFIG_NAME = "atlas_ops.yml"


class ConfigError(Exception):
    """Raised when the Atlas Ops configuration is invalid."""


@dataclass
class Requirement:
    name: str
    check: str
    description: str | None = None


@dataclass
class TaskStep:
    command: str
    workdir: Optional[Path] = None


@dataclass
class Task:
    name: str
    description: str
    steps: List[TaskStep] = field(default_factory=list)


@dataclass
class AtlasConfig:
    project: str
    environment: str
    requirements: List[Requirement] = field(default_factory=list)
    tasks: Dict[str, Task] = field(default_factory=dict)


def _load_yaml(path: Path) -> dict:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}
    except FileNotFoundError as exc:  # pragma: no cover - defensive guard
        raise ConfigError(f"Configuration file not found: {path}") from exc
    except yaml.YAMLError as exc:  # pragma: no cover - defensive guard
        raise ConfigError(f"Failed to parse YAML from {path}") from exc


def _parse_requirements(raw: List[dict]) -> List[Requirement]:
    requirements: List[Requirement] = []
    for item in raw:
        try:
            requirements.append(
                Requirement(
                    name=item["name"],
                    check=item["check"],
                    description=item.get("description"),
                )
            )
        except KeyError as exc:  # pragma: no cover - defensive guard
            raise ConfigError("Requirement entries must include 'name' and 'check'") from exc
    return requirements


def _parse_tasks(raw: Dict[str, dict]) -> Dict[str, Task]:
    tasks: Dict[str, Task] = {}
    for name, details in raw.items():
        steps = [
            TaskStep(command=step["run"], workdir=Path(step["workdir"]) if "workdir" in step else None)
            for step in details.get("steps", [])
        ]
        tasks[name] = Task(
            name=name,
            description=details.get("description", ""),
            steps=steps,
        )
    return tasks


def load_config(path: Optional[Path] = None) -> AtlasConfig:
    """Load the Atlas Ops configuration from disk.

    If ``path`` is not provided, the loader searches for ``atlas_ops.yml`` in the
    current directory and parent directories until it finds one.
    """

    config_path = path or _find_default_config()
    raw = _load_yaml(config_path)

    try:
        project = raw["project"]
        environment = raw.get("environment", "local")
    except KeyError as exc:  # pragma: no cover - defensive guard
        raise ConfigError("Configuration requires a 'project' key") from exc

    requirements_raw = raw.get("requirements", [])
    tasks_raw = raw.get("tasks", {})

    return AtlasConfig(
        project=project,
        environment=environment,
        requirements=_parse_requirements(requirements_raw),
        tasks=_parse_tasks(tasks_raw),
    )


def _find_default_config() -> Path:
    cwd = Path.cwd()
    for candidate in [cwd, *cwd.parents]:
        path = candidate / DEFAULT_CONFIG_NAME
        if path.exists():
            return path
    raise ConfigError(
        f"No {DEFAULT_CONFIG_NAME} found in {cwd} or any parent directories. "
        "Provide --config to specify a custom path."
    )
