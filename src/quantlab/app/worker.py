"""Spawned worker. Must stay importable without Qt (macOS spawn)."""

from __future__ import annotations

import json
import multiprocessing as mp
from pathlib import Path
from typing import Any

from quantlab.app.commands import execute_momentum_backtest, execute_momentum_validation
from quantlab.app.jobs import Job, JobStatus


def backtest_entry(parameters: dict[str, Any], ledger: str, out_file: str) -> None:
    job = Job(
        job_id="child",
        type="backtest",
        status=JobStatus.RUNNING,
        created_at="",
        parameters=parameters,
    )
    result = execute_momentum_backtest(job, Path(ledger))
    Path(out_file).write_text(json.dumps(result, default=str), encoding="utf-8")


def validation_entry(
    parameters: dict[str, Any], ledger: str, artifacts: str, out_file: str
) -> None:
    job = Job(
        job_id="child",
        type="validate",
        status=JobStatus.RUNNING,
        created_at="",
        parameters=parameters,
    )
    result = execute_momentum_validation(job, Path(ledger), artifacts_dir=Path(artifacts))
    Path(out_file).write_text(json.dumps(result, default=str), encoding="utf-8")


def run_backtest_spawned(job: Job, ledger_path: Path) -> dict[str, Any]:
    """Run the slice in a spawned process so Qt never shares a process with numpy."""
    return _spawn(job, ledger_path, backtest_entry, (dict(job.parameters), str(ledger_path)))


def run_validation_spawned(job: Job, ledger_path: Path, artifacts_dir: Path) -> dict[str, Any]:
    return _spawn(
        job,
        ledger_path,
        validation_entry,
        (dict(job.parameters), str(ledger_path), str(artifacts_dir)),
        name=f"quantlab-validate-{job.job_id[:8]}",
    )


def _spawn(
    job: Job,
    ledger_path: Path,
    target: Any,
    args: tuple[Any, ...],
    name: str | None = None,
) -> dict[str, Any]:
    out_file = ledger_path.parent / f"{job.job_id}.result.json"
    ctx = mp.get_context("spawn")
    proc = ctx.Process(
        target=target,
        args=(*args, str(out_file)),
        name=name or f"quantlab-backtest-{job.job_id[:8]}",
    )
    proc.start()
    while proc.is_alive():
        if job.cancel_event.wait(0.1):
            proc.terminate()
            proc.join(timeout=3)
            raise RuntimeError("cancelled")
        job.progress = min(0.85, job.progress + 0.02)
    proc.join()
    if job.cancel_event.is_set():
        raise RuntimeError("cancelled")
    if proc.exitcode != 0:
        raise RuntimeError(f"worker exited {proc.exitcode}")
    if not out_file.exists():
        raise RuntimeError("worker produced no result")
    payload: dict[str, Any] = json.loads(out_file.read_text(encoding="utf-8"))
    out_file.unlink(missing_ok=True)
    return payload
