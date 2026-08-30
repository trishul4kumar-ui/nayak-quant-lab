"""Digital-twin ledger rows. Shadow ≠ live."""

from __future__ import annotations

from contextlib import suppress
from pathlib import Path

from quantlab import __version__
from quantlab.digital_twin.models import TwinRun
from quantlab.digital_twin.service import run_twin
from quantlab.domain.models import ExperimentRun, ExperimentStatus
from quantlab.knowledge.errors import KnowledgeError
from quantlab.models.registry import ExperimentLedger
from quantlab.research.envinfo import environment, git_commit, git_dirty


def _run_row(item: TwinRun) -> ExperimentRun:
    return ExperimentRun(
        id=item.run_id,
        name=f"digital-twin:{item.run_id}",
        hypothesis="A digital twin is not a broker.",
        status=ExperimentStatus.PASSED,
        git_commit=git_commit(),
        dataset_version="digital-twin",
        universe=[],
        feature_versions={},
        label_definition="not_applicable",
        hyperparameters={"seed": 0},
        transaction_cost_bps=10.0,
        snapshot_id=item.snapshot_hash,
        data_kind="synthetic",
        application_version=__version__,
        python_version=environment().get("python", ""),
        git_dirty=git_dirty(),
        selection_stage="digital_twin",
        decision_hash=item.decision_hash,
        reconciliation_hash=item.reconciliation_hash,
        twin_run_id=item.run_id,
        twin_state_hash=item.state_hash,
        twin_replay_hash=item.state_hash,
        realtime_snapshot_hash=item.snapshot_hash,
        realtime_decision_hash=item.decision_hash,
        release_blocked=True,
        shadow_mode=item.mode.value,
    )


def persist_twin(item: TwinRun, ledger_path: Path) -> None:
    from quantlab.knowledge.ingest import persist_digital_twin as ingest_persist

    with suppress(KnowledgeError, OSError):
        ingest_persist(item, ledger_path)


def run_twin_experiment(
    *,
    ledger_path: Path | None = None,
) -> tuple[TwinRun, ExperimentRun]:
    item = run_twin()
    row = _run_row(item)
    path = ledger_path or Path("experiments/ledger.jsonl")
    ExperimentLedger(path).append(row)
    persist_twin(item, path)
    return item, row
