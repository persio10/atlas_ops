from __future__ import annotations

import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

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
    def __init__(self, stream_output: bool = True) -> None:
        self.stream_output = stream_output

    def run_step(self, step: TaskStep) -> StepResult:
        start = time.perf_counter()
        process = subprocess.run(
            step.command,
            shell=True,
            cwd=step.workdir,
            text=True,
            capture_output=not self.stream_output,
            check=False,
        )
        duration = time.perf_counter() - start

        output = process.stdout if process.stdout else ""
        if self.stream_output:
            output = process.stdout or ""
        else:
            combined_output = "".join(
                part for part in [process.stdout, process.stderr] if part is not None
            )
            output = combined_output

        if process.stderr and self.stream_output:
            sys.stderr.write(process.stderr)
            sys.stderr.flush()

        return StepResult(step=step, returncode=process.returncode, output=output, duration=duration)

    def run_task(self, task: Task) -> TaskResult:
        results: List[StepResult] = []
        for step in task.steps:
            results.append(self.run_step(step))
            if not results[-1].ok:
                break
        return TaskResult(task=task, steps=results)


def run_tasks(tasks: Iterable[Task], stream_output: bool = True) -> List[TaskResult]:
    runner = CommandRunner(stream_output=stream_output)
    return [runner.run_task(task) for task in tasks]
