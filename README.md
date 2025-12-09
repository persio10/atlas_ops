# Atlas Ops

Atlas Ops is a lightweight automation toolkit that turns a simple YAML file into repeatable workflows for your platform operations. It focuses on portability: the same configuration can validate local tooling, orchestrate task chains, and bootstrap new contributors.

## Features

- **Declarative tasks**: Define any number of tasks with ordered shell commands.
- **Environment validation**: Encode prerequisite checks (e.g., `docker info`, `terraform --version`).
- **Zero friction**: Ship a single `atlas_ops.yml` alongside your repository and run it with `atlas-ops`.
- **Starter template**: Generate a configuration scaffold with sensible defaults.

## Getting started

1. Install the CLI (editable install from this repository):

   ```bash
   pip install -e .
   ```

2. Generate a template configuration if you do not already have one:

   ```bash
   atlas-ops init
   ```

3. List available tasks defined in `atlas_ops.yml`:

   ```bash
   atlas-ops tasks list
   ```

4. Run a task by name:

   ```bash
   atlas-ops tasks run bootstrap
   ```

5. Validate that required tools exist locally:

   ```bash
   atlas-ops env check
   ```

## Configuration reference

Atlas Ops reads a YAML file (default: `atlas_ops.yml`) with three top-level keys:

- `project`: Display name for your service.
- `environment`: Optional environment label (dev, staging, production).
- `requirements`: A list of tooling checks. Each entry has:
  - `name`: Tool identifier.
  - `check`: Shell command used to verify the tool.
  - `description` (optional): Extra context for the check.
- `tasks`: A mapping of task names to their definitions. Each task includes:
  - `description`: Human-readable summary.
  - `steps`: An ordered list of commands with an optional `workdir` key for per-step working directories.

See [`atlas_ops.yml.example`](atlas_ops.yml.example) for a pre-built configuration you can copy into your own repository.

## Development

The codebase is intentionally small:

- `src/atlas_ops/cli.py` – Typer-based CLI entrypoint.
- `src/atlas_ops/config.py` – YAML loader and configuration validation.
- `src/atlas_ops/executor.py` – Command runner that streams output.
- `src/atlas_ops/templates.py` – Default configuration template for `atlas-ops init`.

You can run a quick import check with Python's standard library:

```bash
python -m compileall src
```

## License

MIT
