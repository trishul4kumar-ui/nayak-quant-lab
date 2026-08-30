"""Safety integrity mapping. Unset flags remain NOT_TESTED in evaluate_integrity."""

from __future__ import annotations

from quantlab.domain.research import IntegrityReport
from quantlab.research.integrity import evaluate_integrity
from quantlab.safety.models import SafetyResult


def report_from_result(result: SafetyResult) -> IntegrityReport:
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
        ai_safety_override="ai_safety_override" in kinds,
    )
