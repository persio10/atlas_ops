from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import typer
import uvicorn

from . import __version__
from .agent import AgentConfig, load_agent_config, run_loop, run_once, save_agent_config
from .backend import BackendSettings, SignalStore, create_app, load_backend_config, save_backend_config
from .config import AtlasConfig, ConfigError, find_default_config, load_config
from .executor import run_tasks
from .templates import CONFIG_TEMPLATE, TASKS_HELP

app = typer.Typer(help="Atlas Ops automation CLI")
task_app = typer.Typer(help="Work with configured tasks")
env_app = typer.Typer(help="Validate local tooling requirements")
config_app = typer.Typer(help="Inspect configuration")
backend_app = typer.Typer(help="Manage backend settings")
agent_app = typer.Typer(help="Manage the Atlas Ops agent")
db_app = typer.Typer(help="Database operations")

app.add_typer(task_app, name="tasks")
app.add_typer(env_app, name="env")
app.add_typer(config_app, name="config")
app.add_typer(backend_app, name="install")
app.add_typer(agent_app, name="agent")
app.add_typer(db_app, name="db")


@app.command()
def version() -> None:
    """Print the installed Atlas Ops version."""

    typer.echo(__version__)


@app.command()
def init(
    path: Path = typer.Option(Path("atlas_ops.yml"), help="Where to write the template configuration."),
    force: bool = typer.Option(False, "--force", help="Overwrite an existing file if present."),
) -> None:
    """Write a starter automation configuration file."""

    if path.exists() and not force:
        typer.echo(f"Configuration already exists at {path}. Use --force to overwrite.")
        raise typer.Exit(code=1)

    path.write_text(CONFIG_TEMPLATE.strip() + "\n", encoding="utf-8")
    typer.echo(f"Created template configuration at {path}")


@app.command()
def serve(
    config: Path = typer.Option(Path("atlas_ops.config.yaml"), help="Backend configuration path"),
) -> None:
    """Start the Atlas Ops backend server."""

    settings = _load_backend_or_exit(config)
    store = SignalStore(settings.db_url)
    app_instance = create_app(settings, store)
    uvicorn.run(app_instance, host=settings.host, port=settings.port)


@backend_app.command("backend")
def install_backend(
    config: Path = typer.Option(Path("atlas_ops.config.yaml"), help="Where to write backend settings."),
    host: str = typer.Option(None, help="Bind host", show_default=False),
    port: int = typer.Option(None, help="Bind port", show_default=False),
    db_url: str = typer.Option(None, help="Database URL", show_default=False),
    shared_token: str = typer.Option(None, help="Shared bearer token", show_default=False),
    allow_origins: Optional[List[str]] = typer.Option(None, help="Allowed CORS origins", show_default=False),
    force: bool = typer.Option(False, "--force", help="Overwrite any existing file"),
    no_interactive: bool = typer.Option(
        False, "--no-interactive", help="Skip prompts and use defaults/flags"
    ),
) -> None:
    """Create backend configuration for the API server."""

    if config.exists() and not force:
        typer.echo(f"Backend config already exists at {config}. Use --force to overwrite.")
        raise typer.Exit(code=1)

    base = BackendSettings()
    settings = BackendSettings(
        host=host or base.host,
        port=port or base.port,
        db_url=db_url or base.db_url,
        shared_token=shared_token or base.shared_token,
        allow_origins=allow_origins or base.allow_origins,
        sites=base.sites,
    )

    save_backend_config(config, settings)
    typer.echo(f"Wrote backend configuration to {config}")


@agent_app.command("install")
def install_agent(
    config: Path = typer.Option(Path("agent_config.yaml"), help="Where to write agent settings."),
    backend_url: str = typer.Option(None, help="Backend base URL", show_default=False),
    shared_token: str = typer.Option(None, help="Shared token", show_default=False),
    docker_host: Optional[List[str]] = typer.Option(None, help="Docker hosts to poll", show_default=False),
    poll_interval: int = typer.Option(None, help="Seconds between polls", show_default=False),
    force: bool = typer.Option(False, "--force", help="Overwrite any existing file"),
    no_interactive: bool = typer.Option(
        False, "--no-interactive", help="Skip prompts and use defaults/flags"
    ),
) -> None:
    """Create agent configuration for polling Docker hosts."""

    if config.exists() and not force:
        typer.echo(f"Agent config already exists at {config}. Use --force to overwrite.")
        raise typer.Exit(code=1)

    base = AgentConfig()
    agent_cfg = AgentConfig(
        backend_url=backend_url or base.backend_url,
        shared_token=shared_token or base.shared_token,
        docker_hosts=docker_host or base.docker_hosts,
        poll_interval=poll_interval or base.poll_interval,
    )
    save_agent_config(config, agent_cfg)
    typer.echo(f"Wrote agent configuration to {config}")


@agent_app.command("run")
def run_agent(
    config: Path = typer.Option(Path("agent_config.yaml"), help="Agent configuration path"),
    once: bool = typer.Option(False, "--once", help="Execute a single poll then exit."),
) -> None:
    """Run the Atlas Ops agent."""

    agent_cfg = _load_agent_or_exit(config)
    if once:
        run_once(agent_cfg)
    else:
        run_loop(agent_cfg)


@db_app.command("migrate")
def migrate_db(config: Path = typer.Option(Path("atlas_ops.config.yaml"), help="Backend configuration path")) -> None:
    """Initialize or migrate the SQLite database."""

    settings = _load_backend_or_exit(config)
    store = SignalStore(settings.db_url)
    store.migrate()
    typer.echo("Database ready ✅")


@config_app.command("path")
def show_path() -> None:
    """Show the resolved automation configuration path."""

    cfg_path = find_default_config()
    typer.echo(str(cfg_path))


@config_app.command("validate")
def validate(config: Optional[Path] = typer.Option(None, "--config", help="Path to the atlas_ops.yml file.")) -> None:
    """Validate the automation configuration and exit non-zero on errors."""

    _load_or_exit(config)
    typer.echo("Configuration looks good ✅")


@task_app.command("list")
def list_tasks(config: Optional[Path] = typer.Option(None, "--config", help="Path to the atlas_ops.yml file.")) -> None:
    """List available tasks from the automation configuration."""

    cfg = _load_or_exit(config)
    typer.echo(f"Tasks for project '{cfg.project}' ({cfg.environment}):")
    for name, task in cfg.tasks.items():
        step_count = len(task.steps)
        typer.echo(f"- {name}: {task.description or 'no description'} ({step_count} step{'s' if step_count != 1 else ''})")


@task_app.command("run")
def run(
    names: List[str] = typer.Argument(..., help="Task names to run in order."),
    config: Optional[Path] = typer.Option(None, "--config", help="Path to the atlas_ops.yml file."),
    stop_on_error: bool = typer.Option(True, help="Stop executing further tasks after a failure."),
) -> None:
    """Run one or more tasks from the automation configuration."""

    cfg = _load_or_exit(config)
    missing = [name for name in names if name not in cfg.tasks]
    if missing:
        typer.echo(f"Unknown task(s): {', '.join(missing)}")
        typer.echo(f"Available: {', '.join(cfg.tasks)}")
        raise typer.Exit(code=1)

    selected = [cfg.tasks[name] for name in names]
    typer.echo(f"Running {len(selected)} task(s) defined for {cfg.project} ({cfg.environment})...\n")
    results = run_tasks(selected, stop_on_error=stop_on_error)

    for task_result in results:
        typer.echo(f"Task '{task_result.task.name}':")
        for idx, step_result in enumerate(task_result.steps, start=1):
            status = "✅" if step_result.ok else "❌"
            location = f" (cwd: {step_result.step.workdir})" if step_result.step.workdir else ""
            typer.echo(f"  {status} Step {idx}: {step_result.step.command}{location}")
            if not step_result.ok:
                typer.echo(f"     ↳ exited with code {step_result.returncode}")
                if stop_on_error:
                    break

    failures = [task for task in results if not task.ok]
    if failures:
        typer.echo(f"\n{len(failures)} task(s) failed")
        raise typer.Exit(code=1)

    typer.echo("\nAll tasks completed successfully.")


@env_app.command("check")
def check_requirements(config: Optional[Path] = typer.Option(None, "--config", help="Path to the atlas_ops.yml file.")) -> None:
    """Validate local tooling versions defined in the automation configuration."""

    cfg = _load_or_exit(config)
    if not cfg.requirements:
        typer.echo("No tooling requirements defined; skipping checks.")
        return

    failures = 0
    for requirement in cfg.requirements:
        typer.echo(f"Checking {requirement.name}...")
        exit_code = typer.shell(command=requirement.check)
        if exit_code != 0:
            failures += 1
            typer.echo(f"❌ {requirement.name} failed with exit code {exit_code}")
        else:
            typer.echo(f"✅ {requirement.name} is available")

    if failures:
        typer.echo(f"\n{failures} requirement(s) failed. Please address them before continuing.")
        raise typer.Exit(code=failures)

    typer.echo("\nAll requirements satisfied.")


@env_app.command("example")
def show_task_examples() -> None:
    """Print sample tasks to copy into your automation configuration."""

    typer.echo(TASKS_HELP.strip())


def _load_or_exit(path: Optional[Path]) -> AtlasConfig:
    try:
        return load_config(path)
    except ConfigError as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=1)


def _load_backend_or_exit(path: Path) -> BackendSettings:
    if not path.exists():
        typer.echo(f"Backend configuration not found at {path}")
        raise typer.Exit(code=1)
    return load_backend_config(path)


def _load_agent_or_exit(path: Path) -> AgentConfig:
    if not path.exists():
        typer.echo(f"Agent configuration not found at {path}")
        raise typer.Exit(code=1)
    return load_agent_config(path)


if __name__ == "__main__":
    app()
