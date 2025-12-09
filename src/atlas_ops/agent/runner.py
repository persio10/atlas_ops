from __future__ import annotations

import os
import subprocess
import time
from typing import Iterable

import httpx

from .config import AgentConfig


def _check_docker(host: str) -> dict:
    env = os.environ.copy()
    env["DOCKER_HOST"] = host
    result = subprocess.run(["docker", "ps"], env=env, capture_output=True, text=True)
    status = "ok" if result.returncode == 0 else "error"
    details = result.stdout or result.stderr
    return {"host": host, "status": status, "message": details.strip()}


def gather_signals(config: AgentConfig) -> Iterable[dict]:
    for host in config.docker_hosts:
        yield {"name": "docker_host", "status": "ok", "details": _check_docker(host)}


def _post_signal(config: AgentConfig, signal: dict) -> None:
    headers = {"Authorization": f"Bearer {config.shared_token}"}
    with httpx.Client(base_url=config.backend_url, timeout=10.0) as client:
        client.post("/api/signals", json=signal, headers=headers)


def run_once(config: AgentConfig) -> None:
    for signal in gather_signals(config):
        try:
            _post_signal(config, signal)
        except Exception:
            continue


def run_loop(config: AgentConfig) -> None:
    while True:
        run_once(config)
        time.sleep(config.poll_interval)

