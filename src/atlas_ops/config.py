from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, MutableMapping, Optional

import yaml

DEFAULT_CONFIG_NAME = "atlas_ops.yml"


class ConfigError(Exception):
    """Raised when the Atlas Ops configuration is invalid."""


@dataclass
class Requirement:
    """Represents a prerequisite check for the local environment."""

    name: str
    check: str
    description: str | None = None


@dataclass
class TaskStep:
    """Single executable command inside a task."""

    command: str
    workdir: Optional[Path] = None
    env: Dict[str, str] = field(default_factory=dict)


@dataclass
class Task:
    """Named collection of ordered task steps."""

    name: str
    description: str
    steps: List[TaskStep] = field(default_factory=list)

    def validate(self) -> None:
        if not self.steps:
            raise ConfigError(f"Task '{self.name}' must define at least one step")
        for index, step in enumerate(self.steps, start=1):
            if not step.command:
                raise ConfigError(f"Task '{self.name}' step {index} is missing a 'run' command")


@dataclass
class AtlasConfig:
    """Top-level Atlas Ops configuration model."""

    project: str
    environment: str
    requirements: List[Requirement] = field(default_factory=list)
    tasks: Dict[str, Task] = field(default_factory=dict)
    source_path: Optional[Path] = None

    def validate(self) -> None:
        if not self.project:
            raise ConfigError("Configuration requires a 'project' name")
        if not self.tasks:
            raise ConfigError("Configuration must define at least one task under 'tasks'")
        for task in self.tasks.values():
            task.validate()


def _load_yaml(path: Path) -> MutableMapping:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}
    except FileNotFoundError as exc:  # pragma: no cover - defensive guard
        raise ConfigError(f"Configuration file not found: {path}") from exc
    except yaml.YAMLError as exc:  # pragma: no cover - defensive guard
        raise ConfigError(f"Failed to parse YAML from {path}") from exc


def _parse_requirements(raw: Iterable[Mapping]) -> List[Requirement]:
    if raw is None:
        return []
    if not isinstance(raw, Iterable) or isinstance(raw, (str, bytes)):
        raise ConfigError("'requirements' must be a list of mappings")

    requirements: List[Requirement] = []
    for item in raw:
        if not isinstance(item, Mapping):
            raise ConfigError("Each requirement entry must be a mapping")
        if "name" not in item or "check" not in item:
            raise ConfigError("Requirement entries must include 'name' and 'check'")
        requirements.append(
            Requirement(
                name=str(item["name"]),
                check=str(item["check"]),
                description=str(item.get("description")) if item.get("description") else None,
            )
        )
    return requirements


def _parse_task_step(raw: Mapping) -> TaskStep:
    if not isinstance(raw, Mapping):
        raise ConfigError("Each task step must be a mapping")

    if "run" not in raw:
        raise ConfigError("Task steps must include a 'run' command")

    workdir_value = raw.get("workdir")
    workdir = Path(workdir_value) if workdir_value else None
    env_raw = raw.get("env") or {}
    if not isinstance(env_raw, Mapping):
        raise ConfigError("Task step 'env' must be a mapping of environment variables")

    env = {str(key): str(value) for key, value in env_raw.items()}
    return TaskStep(command=str(raw["run"]), workdir=workdir, env=env)


def _parse_tasks(raw: Mapping[str, Mapping]) -> Dict[str, Task]:
    if not isinstance(raw, Mapping):
        raise ConfigError("Top-level 'tasks' must be a mapping")

    tasks: Dict[str, Task] = {}
    for name, details in raw.items():
        if not isinstance(details, Mapping):
            raise ConfigError("Task definitions must be mappings")
        description = str(details.get("description", "")).strip()
        steps_raw = details.get("steps", [])
        if not isinstance(steps_raw, Iterable) or isinstance(steps_raw, (str, bytes)):
            raise ConfigError(f"Task '{name}' steps must be a list")
        steps = [_parse_task_step(step) for step in steps_raw]
        tasks[name] = Task(name=name, description=description, steps=steps)
    return tasks


def load_config(path: Optional[Path] = None) -> AtlasConfig:
    """Load and validate an Atlas Ops configuration file."""

    config_path = path or find_default_config()
    raw = _load_yaml(config_path)

    if "project" not in raw:
        raise ConfigError("Configuration requires a top-level 'project' key")

    project = str(raw.get("project"))
    environment = str(raw.get("environment", "local"))
    requirements_raw = raw.get("requirements", [])
    tasks_raw = raw.get("tasks", {})

    config = AtlasConfig(
        project=project,
        environment=environment,
        requirements=_parse_requirements(requirements_raw),
        tasks=_parse_tasks(tasks_raw),
        source_path=config_path,
    )
    config.validate()
    return config


def find_default_config(start: Optional[Path] = None) -> Path:
    """Find ``atlas_ops.yml`` by walking up from ``start`` (defaults to CWD)."""

    cwd = start or Path.cwd()
    for candidate in [cwd, *cwd.parents]:
        path = candidate / DEFAULT_CONFIG_NAME
        if path.exists():
            return path
    raise ConfigError(
        f"No {DEFAULT_CONFIG_NAME} found in {cwd} or parent directories. "
        "Provide --config to specify a custom path."
    )
