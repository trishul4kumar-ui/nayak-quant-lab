"""Safety ledger rows. Reuses JSONL ExperimentLedger."""

from __future__ import annotations

from contextlib import suppress
from pathlib import Path

from quantlab import __version__
from quantlab.domain.models import ExperimentRun, ExperimentStatus
from quantlab.knowledge.errors import KnowledgeError
from quantlab.models.registry import ExperimentLedger
from quantlab.research.envinfo import environment, git_commit, git_dirty
from quantlab.safety.models import SafetyRequest, SafetyResult
from quantlab.safety.repository import put
from quantlab.safety.service import evaluate_request


def _run_row(result: SafetyResult) -> ExperimentRun:
    auth_id = result.authorization.authorization_id if result.authorization else ""
    return ExperimentRun(
        id=result.evaluation_id,
        name=f"safety:{result.state.value}",
        hypothesis="Safety evaluation is not a live order.",
        status=ExperimentStatus.PASSED if result.blocked else ExperimentStatus.FAILED,
        git_commit=git_commit(),
        dataset_version="safety",
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
        authorization_id=auth_id,
        safety_state=result.state.value,
        kill_switch_active=True,
        release_blocked=True,
    )


def persist_safety(result: SafetyResult, ledger_path: Path) -> None:
    from quantlab.knowledge.ingest import persist_safety as ingest_persist

    with suppress(KnowledgeError, OSError):
        ingest_persist(result, ledger_path)


def run_safety_experiment(
    request: SafetyRequest | None = None,
    *,
    ledger_path: Path | None = None,
) -> tuple[SafetyResult, ExperimentRun]:
    result = evaluate_request(request)
    put(result)
    row = _run_row(result)
    path = ledger_path or Path("experiments/ledger.jsonl")
    ExperimentLedger(path).append(row)
    persist_safety(result, path)
    return result, row
