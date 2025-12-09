# Atlas Ops Copilot

Atlas Ops is a lightweight automation and incident assistant. It ships a Typer CLI, FastAPI backend, dashboard UI, and an optional agent that can watch Docker hosts and push signals into the backend.

## Features

- Declarative task runner from `atlas_ops.yml` with requirement checks
- FastAPI backend serving `/api` plus a bundled static dashboard under `/frontend`
- Simple SQLite-backed signal store with runbook and suggestion endpoints
- Agent that polls Docker and forwards status signals
- Docker image and Compose file for a one-command launch

## Quickstart (Docker)

```bash
git clone <repo-url>
cd atlas_ops
cp .env.example .env  # edit ATLAS_OPS_SHARED_TOKEN or port as needed
docker compose up --build -d
# open http://localhost:8000/frontend/
```

The container will write `/data/atlas_ops.config.yaml` if missing, migrate the SQLite DB, and start the API + UI.

## Quickstart (local dev)

```bash
git clone <repo-url>
cd atlas_ops
python -m pip install -r requirements.txt
python -m pip install .

atlas-ops install backend --config atlas_ops.config.yaml
atlas-ops db migrate --config atlas_ops.config.yaml
atlas-ops serve --config atlas_ops.config.yaml
# open http://localhost:8000/frontend/
```

Agent example:

```bash
atlas-ops install agent --config agent_config.yaml --backend-url http://localhost:8000 --shared-token <token>
atlas-ops agent run --config agent_config.yaml --once  # smoke test
```

## CLI commands

- `atlas-ops init` – scaffold a starter `atlas_ops.yml`
- `atlas-ops tasks list|run` – inspect or execute automation tasks
- `atlas-ops env check|example` – validate tooling or show task snippets
- `atlas-ops install backend` – create backend YAML config
- `atlas-ops db migrate` – ensure the SQLite schema exists
- `atlas-ops serve` – launch the FastAPI server with static frontend
- `atlas-ops install agent` – write agent YAML config
- `atlas-ops agent run [--once]` – run the polling agent

## Configuration

Backend config (written via `atlas-ops install backend`):

```yaml
host: 0.0.0.0
port: 8000
db_url: sqlite:////data/atlas_ops.db
shared_token: changeme
allow_origins:
  - "*"
sites:
  - name: local-docker
    description: Local Docker host
    host: localhost
```

Agent config:

```yaml
backend_url: http://localhost:8000
shared_token: changeme
docker_hosts:
  - unix:///var/run/docker.sock
poll_interval: 60
```

Automation config (tasks/requirements): see `atlas_ops.yml.example`.

## Development

- Source lives in `src/atlas_ops`
- Frontend assets live in `src/atlas_ops/frontend`
- Run a quick sanity check with `python -m compileall src`

## License

MIT
