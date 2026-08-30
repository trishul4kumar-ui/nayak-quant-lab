"""Real-time data ledger rows. Observe-only."""

from __future__ import annotations

from contextlib import suppress
from pathlib import Path

from quantlab import __version__
from quantlab.domain.models import ExperimentRun, ExperimentStatus
from quantlab.knowledge.errors import KnowledgeError
from quantlab.models.registry import ExperimentLedger
from quantlab.realtime_data.models import RealTimeSnapshot
from quantlab.realtime_data.service import snapshot
from quantlab.research.envinfo import environment, git_commit, git_dirty


def _run_row(frozen: RealTimeSnapshot) -> ExperimentRun:
    return ExperimentRun(
        id=frozen.snapshot_id,
        name=f"realtime-data:{frozen.snapshot_id}",
        hypothesis="Frozen MarketState(T) is observation, not a trade.",
        status=ExperimentStatus.PASSED,
        git_commit=git_commit(),
        dataset_version="realtime-data",
        universe=[],
        feature_versions={},
        label_definition="not_applicable",
        hyperparameters={"seed": 0},
        transaction_cost_bps=10.0,
        snapshot_id=frozen.snapshot_id,
        data_kind="synthetic",
        application_version=__version__,
        python_version=environment().get("python", ""),
        git_dirty=git_dirty(),
        selection_stage="realtime_data",
        calendar_version=frozen.calendar_version,
        realtime_snapshot_id=frozen.snapshot_id,
        realtime_snapshot_hash=frozen.snapshot_hash,
        release_blocked=True,
    )


def persist_realtime(frozen: RealTimeSnapshot, ledger_path: Path) -> None:
    from quantlab.knowledge.ingest import persist_realtime_data as ingest_persist

    with suppress(KnowledgeError, OSError):
        ingest_persist(frozen, ledger_path)


def run_realtime_experiment(
    *,
    ledger_path: Path | None = None,
) -> tuple[RealTimeSnapshot, ExperimentRun]:
    frozen = snapshot()
    row = _run_row(frozen)
    path = ledger_path or Path("experiments/ledger.jsonl")
    ExperimentLedger(path).append(row)
    persist_realtime(frozen, path)
    return frozen, row
