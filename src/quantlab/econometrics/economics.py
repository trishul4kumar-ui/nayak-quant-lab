"""Statistical vs economic vs execution-adjusted significance."""

from __future__ import annotations

from quantlab.backtest.costs import CostSchedule
from quantlab.domain.research import CheckResult
from quantlab.econometrics.models import EconomicSignificance
from quantlab.execution_research.costs import explicit_bps


def economic_report(
    *,
    statistic: float | None,
    effect: float | None,
    cost_bps: float,
) -> EconomicSignificance:
    if statistic is None or effect is None:
        return EconomicSignificance(
            statistical=CheckResult.NOT_TESTED,
            economic_effect=effect,
            execution_adjusted=None,
            robust=CheckResult.NOT_TESTED,
            status=CheckResult.NOT_TESTED,
            note="Insufficient evidence. P-value is not economic value.",
        )
    schedule = CostSchedule(commission_bps=cost_bps, provenance="configured_research")
    cost = explicit_bps(schedule) / 10_000.0
    adjusted = effect - cost
    return EconomicSignificance(
        statistical=CheckResult.PASS,
        economic_effect=effect,
        execution_adjusted=adjusted,
        robust=CheckResult.PASS if adjusted > 0 else CheckResult.WARN,
        status=CheckResult.PASS,
        note=(
            "Execution-adjusted uses Prompt 13 explicit bps. "
            "A positive statistic is not a claim and not a live edge."
        ),
    )
