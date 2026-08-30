"""Canonical hashes for monitoring objects."""

from __future__ import annotations

from typing import Any

from quantlab.backtest.spec import config_hash
from quantlab.monitoring.models import (
    AttributionResult,
    DriftObservation,
    MonitoringRun,
    PerformanceSnapshot,
    PnLBreakdown,
    ResearchFeedback,
)


def _dump(payload: dict[str, Any]) -> str:
    return config_hash(payload)


def hash_pnl(pnl: PnLBreakdown) -> str:
    return _dump(pnl.model_dump(mode="json", exclude={"note"}))


def hash_snapshot(snapshot: PerformanceSnapshot) -> str:
    return _dump(
        snapshot.model_dump(mode="json", exclude={"snapshot_hash", "note"})
    )


def hash_attribution(result: AttributionResult) -> str:
    return _dump(result.model_dump(mode="json", exclude={"note"}))


def hash_drift(obs: DriftObservation) -> str:
    return _dump(obs.model_dump(mode="json", exclude={"note"}))


def hash_feedback(item: ResearchFeedback) -> str:
    return _dump(item.model_dump(mode="json", exclude={"note"}))


def hash_run(run: MonitoringRun) -> str:
    return _dump(run.model_dump(mode="json", exclude={"run_hash", "note"}))


def idempotency_key(
    *,
    decision_hash: str,
    oms_run_id: str,
    snapshot_id: str,
    methodology_id: str,
    benchmark_id: str,
) -> str:
    return _dump(
        {
            "decision_hash": decision_hash,
            "oms_run_id": oms_run_id,
            "snapshot_id": snapshot_id,
            "methodology_id": methodology_id,
            "benchmark_id": benchmark_id,
        }
    )
