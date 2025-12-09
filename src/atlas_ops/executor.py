from __future__ import annotations

import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence

from .config import Task, TaskStep


@dataclass
class StepResult:
    step: TaskStep
    returncode: int
    output: str
    duration: float

    @property
    def ok(self) -> bool:
        return self.returncode == 0


@dataclass
class TaskResult:
    task: Task
    steps: List[StepResult]

    @property
    def ok(self) -> bool:
        return all(step.ok for step in self.steps)


class CommandRunner:
    """Execute task steps while streaming output to the console."""

    def __init__(self, stream_output: bool = True) -> None:
        self.stream_output = stream_output

    def run_step(self, step: TaskStep, *, base_env: Dict[str, str] | None = None) -> StepResult:
        env = dict(os.environ)
        if base_env:
            env.update(base_env)
        env.update(step.env)

        start = time.perf_counter()
        process = subprocess.Popen(
            step.command,
            shell=True,
            cwd=step.workdir or Path.cwd(),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env,
        )

        captured_output = []
        assert process.stdout is not None
        for line in process.stdout:
            captured_output.append(line)
            if self.stream_output:
                sys.stdout.write(line)
                sys.stdout.flush()

        process.wait()
        duration = time.perf_counter() - start
        output = "".join(captured_output)
        return StepResult(step=step, returncode=process.returncode or 0, output=output, duration=duration)

    def run_task(self, task: Task, *, base_env: Dict[str, str] | None = None, stop_on_error: bool = True) -> TaskResult:
        results: List[StepResult] = []
        for step in task.steps:
            step_result = self.run_step(step, base_env=base_env)
            results.append(step_result)
            if stop_on_error and not step_result.ok:
                break
        return TaskResult(task=task, steps=results)


def run_tasks(
    tasks: Sequence[Task],
    *,
    stream_output: bool = True,
    base_env: Dict[str, str] | None = None,
    stop_on_error: bool = True,
) -> List[TaskResult]:
    """Run multiple tasks sequentially."""

    runner = CommandRunner(stream_output=stream_output)
    return [runner.run_task(task, base_env=base_env, stop_on_error=stop_on_error) for task in tasks]
