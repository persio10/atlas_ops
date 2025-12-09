from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from .config import AtlasConfig, ConfigError, load_config
from .executor import run_tasks
from .templates import CONFIG_TEMPLATE

app = typer.Typer(help="Atlas Ops automation CLI")
task_app = typer.Typer(help="Work with configured tasks")
env_app = typer.Typer(help="Validate local tooling requirements")
app.add_typer(task_app, name="tasks")
app.add_typer(env_app, name="env")


@app.command()
def init(path: Path = typer.Option(Path("atlas_ops.yml"), help="Where to write the template configuration.")) -> None:
    """Write a starter configuration file."""

    if path.exists():
        typer.echo(f"Configuration already exists at {path}. Skipping creation.")
        return

    path.write_text(CONFIG_TEMPLATE.strip() + "\n", encoding="utf-8")
    typer.echo(f"Created template configuration at {path}")


@task_app.command("list")
def list_tasks(config: Optional[Path] = typer.Option(None, "--config", help="Path to the atlas_ops.yml file.")) -> None:
    """List available tasks from the configuration."""

    cfg = _load_or_exit(config)
    if not cfg.tasks:
        typer.echo("No tasks configured yet. Use the template to add some.")
        raise typer.Exit(code=1)

    typer.echo(f"Tasks for project '{cfg.project}' ({cfg.environment}):")
    for name, task in cfg.tasks.items():
        typer.echo(f"- {name}: {task.description}")


@task_app.command()
def run(name: str, config: Optional[Path] = typer.Option(None, "--config", help="Path to the atlas_ops.yml file.")) -> None:
    """Run a named task from the configuration."""

    cfg = _load_or_exit(config)
    if name not in cfg.tasks:
        typer.echo(f"Task '{name}' not found. Available: {', '.join(cfg.tasks.keys())}")
        raise typer.Exit(code=1)

    task = cfg.tasks[name]
    typer.echo(f"Running task '{name}' with {len(task.steps)} steps...\n")
    results = run_tasks([task])
    result = results[0]

    for index, step_result in enumerate(result.steps, start=1):
        status = "✅" if step_result.ok else "❌"
        location = f" (cwd: {step_result.step.workdir})" if step_result.step.workdir else ""
        typer.echo(f"{status} Step {index}: {step_result.step.command}{location}")
        if not step_result.ok:
            typer.echo("Command failed; stopping further execution.")
            raise typer.Exit(code=step_result.returncode)

    typer.echo("\nTask completed successfully.")


@env_app.command("check")
def check_requirements(config: Optional[Path] = typer.Option(None, "--config", help="Path to the atlas_ops.yml file.")) -> None:
    """Validate local tooling versions defined in the configuration."""

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


def _load_or_exit(path: Optional[Path]) -> AtlasConfig:
    try:
        return load_config(path)
    except ConfigError as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
