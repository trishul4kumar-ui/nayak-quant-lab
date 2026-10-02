"""Factor attribution. Reuses Prompt 08 inputs when supplied. No second covariance."""

from __future__ import annotations

from quantlab.domain.research import CheckResult
from quantlab.monitoring.enums import AttributionMethod
from quantlab.monitoring.models import AttributionResult, PnLBreakdown, SecurityContribution


def factor_attribution(
    pnl: PnLBreakdown,
    *,
    factor_returns: dict[str, float] | None,
    factor_exposures: dict[str, float] | None,
) -> AttributionResult:
    if not factor_returns or not factor_exposures:
        return AttributionResult(
            method=AttributionMethod.UNAVAILABLE,
            total=pnl.pnl_total,
            residual=pnl.pnl_total,
            status=CheckResult.NOT_TESTED,
            note=(
                "Factor returns/exposures were not supplied. "
                "NIFTY, sector, and cap series remain NOT_TESTED. "
                "No second covariance engine."
            ),
        )
    contributions: dict[str, float] = {}
    explained = 0.0
    for name, ret in factor_returns.items():
        exposure = factor_exposures.get(name, 0.0)
        piece = exposure * ret * pnl.beginning_equity
        contributions[name] = piece
        explained += piece
    residual = pnl.pnl_total - explained
    rows = [
        SecurityContribution(
            security_id=name,
            pnl=value,
            return_contribution=value / pnl.beginning_equity if pnl.beginning_equity else 0.0,
        )
        for name, value in contributions.items()
    ]
    return AttributionResult(
        method=AttributionMethod.MODEL_BASED,
        total=pnl.pnl_total,
        residual=residual,
        contributions=rows,
        factor_contributions=contributions,
        status=CheckResult.PASS,
        note="Model-based factor attribution. Residual is explicit.",
    )
