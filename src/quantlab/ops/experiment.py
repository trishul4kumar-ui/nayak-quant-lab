"""Ops ledger rows. Reuses JSONL ExperimentLedger."""

from __future__ import annotations

from contextlib import suppress
from pathlib import Path

from quantlab import __version__
from quantlab.domain.models import ExperimentRun, ExperimentStatus
from quantlab.knowledge.errors import KnowledgeError
from quantlab.models.registry import ExperimentLedger
from quantlab.ops.models import OpsResult
from quantlab.ops.repository import put
from quantlab.ops.service import doctor
from quantlab.research.envinfo import environment, git_commit, git_dirty


def _run_row(result: OpsResult) -> ExperimentRun:
    return ExperimentRun(
        id=result.run_id,
        name=f"ops:{result.state.value}",
        hypothesis="Ops control plane is not live trading.",
        status=(
            ExperimentStatus.PASSED if result.health.value != "failed" else ExperimentStatus.FAILED
        ),
        git_commit=git_commit(),
        dataset_version="ops",
        universe=[],
        feature_versions={},
        label_definition="not_applicable",
        hyperparameters={"seed": 0},
        transaction_cost_bps=10.0,
        snapshot_id="",
        data_kind="synthetic",
        application_version=__version__,
        python_version=environment().get("python", ""),
        git_dirty=git_dirty(),
        ops_run_id=result.run_id,
        ops_environment=result.environment.value,
        ops_config_hash=result.config_hash,
        backup_id="",
        process_id="",
        release_blocked=True,
    )


def persist_ops(result: OpsResult, ledger_path: Path) -> None:
    from quantlab.knowledge.ingest import persist_ops as ingest_persist

    with suppress(KnowledgeError, OSError):
        ingest_persist(result, ledger_path)


def run_ops_experiment(*, ledger_path: Path | None = None) -> tuple[OpsResult, ExperimentRun]:
    result = doctor()
    put(result)
    row = _run_row(result)
    path = ledger_path or Path("experiments/ledger.jsonl")
    ExperimentLedger(path).append(row)
    persist_ops(result, path)
    return result, row
