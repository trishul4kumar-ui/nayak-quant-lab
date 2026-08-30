"""Canonical hashes for shadow objects. future_payload_ignored is never hashed."""

from __future__ import annotations

from typing import Any

from quantlab.backtest.spec import config_hash
from quantlab.shadow.models import (
    FrozenSnapshot,
    ShadowCheckpoint,
    ShadowConfig,
    ShadowCycle,
    ShadowFill,
    ShadowOrder,
    ShadowReconciliation,
)


def _dump(payload: dict[str, Any]) -> str:
    return config_hash(payload)


def hash_config(config: ShadowConfig) -> str:
    return _dump(config.model_dump(mode="json", exclude={"configuration_hash", "note"}))


def hash_snapshot(snapshot: FrozenSnapshot) -> str:
    return _dump(snapshot.model_dump(mode="json", exclude={"snapshot_hash", "note"}))


def hash_order(order: ShadowOrder) -> str:
    return _dump(
        order.model_dump(
            mode="json",
            exclude={"note", "status"},
        )
    )


def hash_fill(fill: ShadowFill) -> str:
    return _dump(fill.model_dump(mode="json", exclude={"note"}))


def hash_reconciliation(report: ShadowReconciliation) -> str:
    return _dump(
        report.model_dump(mode="json", exclude={"reconciliation_hash", "report_id", "note"})
    )


def hash_cycle(cycle: ShadowCycle) -> str:
    return _dump(
        cycle.model_dump(
            mode="json",
            exclude={"cycle_id", "run_id", "completed_at", "note"},
        )
    )


def hash_checkpoint(checkpoint: ShadowCheckpoint) -> str:
    return _dump(
        checkpoint.model_dump(mode="json", exclude={"checkpoint_id", "payload_hash", "note"})
    )


def idempotency_key(
    *,
    strategy_version: str,
    decision_time: str,
    data_snapshot_hash: str,
    portfolio_state_hash: str,
    configuration_hash: str,
) -> str:
    return _dump(
        {
            "strategy_version": strategy_version,
            "decision_time": decision_time,
            "data_snapshot_hash": data_snapshot_hash,
            "portfolio_state_hash": portfolio_state_hash,
            "configuration_hash": configuration_hash,
        }
    )
