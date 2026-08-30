"""App-facing econometric report."""

from __future__ import annotations

from typing import Any

from quantlab.econometrics.models import EconometricResult


def result_report(result: EconometricResult) -> dict[str, Any]:
    cause = result.diagnostics.causality
    coint = result.diagnostics.cointegration
    return {
        "econometrics_run_id": result.run.econometrics_run_id,
        "spec_id": result.spec.spec_id,
        "estimator": result.spec.estimator.value,
        "adf_stationary_rejects": (
            None
            if not result.diagnostics.stationarity
            else result.diagnostics.stationarity[0].rejects_unit_root
        ),
        "cointegration": None if coint is None else coint.method.value,
        "granger_claim": None if cause is None else cause.claim.value,
        "family_id": result.multiple_testing.get("family_id", ""),
        "tested_count": result.run.tested_count,
        "live_trading": False,
        "hash": result.run.run_hash,
        "note": result.note,
    }
