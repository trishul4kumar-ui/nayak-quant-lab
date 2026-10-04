"""Canonical hashes for TCA objects."""

from __future__ import annotations

from typing import Any

from quantlab.backtest.spec import config_hash
from quantlab.tca.models import CalibrationRecord, CapacityResult, ShortfallBreakdown, TCARun


def _dump(payload: dict[str, Any]) -> str:
    return config_hash(payload)


def hash_shortfall(item: ShortfallBreakdown) -> str:
    return _dump(item.model_dump(mode="json", exclude={"note"}))


def hash_calibration(item: CalibrationRecord) -> str:
    return _dump(item.model_dump(mode="json", exclude={"parameter_hash", "note"}))


def hash_capacity(item: CapacityResult) -> str:
    return _dump(item.model_dump(mode="json", exclude={"note"}))


def hash_run(run: TCARun) -> str:
    return _dump(run.model_dump(mode="json", exclude={"tca_hash", "note"}))


def idempotency_key(
    *,
    oms_run_id: str,
    kind: str,
    arrival_policy: str,
    snapshot_id: str,
    model_version: str,
    liquidity_evidence: dict[str, Any] | None = None,
) -> str:
    return _dump(
        {
            "oms_run_id": oms_run_id,
            "kind": kind,
            "arrival_policy": arrival_policy,
            "snapshot_id": snapshot_id,
            "model_version": model_version,
            "liquidity_evidence": liquidity_evidence or {},
        }
    )
