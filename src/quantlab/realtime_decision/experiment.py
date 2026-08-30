"""Real-time decision ledger rows. Decision ≠ order."""

from __future__ import annotations

from contextlib import suppress
from pathlib import Path

from quantlab import __version__
from quantlab.domain.models import ExperimentRun, ExperimentStatus
from quantlab.knowledge.errors import KnowledgeError
from quantlab.models.registry import ExperimentLedger
from quantlab.realtime_decision.models import RealTimeDecision, synthetic_research_release
from quantlab.realtime_decision.service import run_realtime_decision
from quantlab.research.envinfo import environment, git_commit, git_dirty


def _run_row(item: RealTimeDecision) -> ExperimentRun:
    return ExperimentRun(
        id=item.decision_id,
        name=f"realtime-decision:{item.decision_id}",
        hypothesis="A target portfolio is not an order.",
        status=ExperimentStatus.PASSED,
        git_commit=git_commit(),
        dataset_version="realtime-decision",
        universe=[],
        feature_versions={},
        label_definition="not_applicable",
        hyperparameters={"seed": 0},
        transaction_cost_bps=10.0,
        snapshot_id=item.snapshot_id,
        data_kind="synthetic",
        application_version=__version__,
        python_version=environment().get("python", ""),
        git_dirty=git_dirty(),
        selection_stage="realtime_decision",
        decision_id=item.decision_id,
        decision_hash=item.decision_hash,
        decision_status=item.state,
        abstention_code=item.abstention.value,
        target_portfolio_hash=item.target.portfolio_hash if item.target else "",
        realtime_snapshot_id=item.snapshot_id,
        realtime_snapshot_hash=item.snapshot_hash,
        strategy_release_id=item.release_id,
        strategy_release_hash=item.release_hash,
        realtime_decision_id=item.decision_id,
        realtime_decision_hash=item.decision_hash,
        release_blocked=True,
    )


def persist_decision(item: RealTimeDecision, ledger_path: Path) -> None:
    from quantlab.knowledge.ingest import persist_realtime_decision as ingest_persist

    with suppress(KnowledgeError, OSError):
        ingest_persist(item, ledger_path)


def run_decision_experiment(
    *,
    ledger_path: Path | None = None,
) -> tuple[RealTimeDecision, ExperimentRun]:
    from quantlab.realtime_data.mock import SEED_AS_OF

    item = run_realtime_decision(release=synthetic_research_release(as_of=SEED_AS_OF))
    row = _run_row(item)
    path = ledger_path or Path("experiments/ledger.jsonl")
    ExperimentLedger(path).append(row)
    persist_decision(item, path)
    return item, row
