"""Ops integrity mapping."""

from __future__ import annotations

from quantlab.domain.research import IntegrityReport
from quantlab.ops.models import OpsResult
from quantlab.research.integrity import evaluate_integrity


def report_from_result(result: OpsResult) -> IntegrityReport:
    kinds = {item.kind for item in result.incidents}
    return evaluate_integrity(
        bars=[],
        states=[],
        as_of_times=[],
        next_bar_fill=True,
        cost_bps=10.0,
        slippage_model="none",
        live_trading=result.live_trading,
        n_experiments_in_family=1,
        used_ml=False,
        operational_bypass="operational_bypass" in kinds,
        safety_halt_failure="safety_halt_failure" in kinds,
    )
