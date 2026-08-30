"""Broker-gateway ledger rows. Credentials never stored."""

from __future__ import annotations

from contextlib import suppress
from pathlib import Path

from quantlab import __version__
from quantlab.broker_gateway.models import GatewaySnapshotBundle
from quantlab.broker_gateway.service import snapshot
from quantlab.domain.models import ExperimentRun, ExperimentStatus
from quantlab.knowledge.errors import KnowledgeError
from quantlab.models.registry import ExperimentLedger
from quantlab.research.envinfo import environment, git_commit, git_dirty


def _run_row(bundle: GatewaySnapshotBundle) -> ExperimentRun:
    return ExperimentRun(
        id=bundle.bundle_id,
        name=f"broker-gateway:{bundle.adapter_id}",
        hypothesis="Broker snapshot is account truth, not a live order.",
        status=ExperimentStatus.PASSED,
        git_commit=git_commit(),
        dataset_version="broker-gateway",
        universe=[],
        feature_versions={},
        label_definition="not_applicable",
        hyperparameters={"seed": 0},
        transaction_cost_bps=10.0,
        snapshot_id=bundle.payload_hash,
        data_kind="synthetic",
        application_version=__version__,
        python_version=environment().get("python", ""),
        git_dirty=git_dirty(),
        selection_stage="broker_gateway",
        broker_connection_id=bundle.connection_id,
        adapter_id=bundle.adapter_id,
        account_snapshot_id=bundle.account.snapshot_id,
        snapshot_hash=bundle.payload_hash,
        gateway_version=__version__,
        release_blocked=True,
    )


def persist_gateway(bundle: GatewaySnapshotBundle, ledger_path: Path) -> None:
    from quantlab.knowledge.ingest import persist_broker_gateway as ingest_persist

    with suppress(KnowledgeError, OSError):
        ingest_persist(bundle, ledger_path)


def run_gateway_experiment(
    *,
    ledger_path: Path | None = None,
) -> tuple[GatewaySnapshotBundle, ExperimentRun]:
    bundle = snapshot()
    row = _run_row(bundle)
    path = ledger_path or Path("experiments/ledger.jsonl")
    ExperimentLedger(path).append(row)
    persist_gateway(bundle, path)
    return bundle, row
