"""Alpha/lineage attribution. Do not invent a split without causal evidence."""

from __future__ import annotations

from quantlab.domain.research import CheckResult
from quantlab.monitoring.enums import AttributionMethod
from quantlab.monitoring.models import AttributionResult, PnLBreakdown, SecurityContribution


def alpha_attribution(
    pnl: PnLBreakdown,
    *,
    lineage: dict[str, float] | None,
) -> AttributionResult:
    if not lineage:
        return AttributionResult(
            method=AttributionMethod.UNAVAILABLE,
            total=pnl.pnl_total,
            residual=pnl.pnl_total,
            status=CheckResult.NOT_TESTED,
            note=(
                "No alpha/model/ensemble lineage weights were supplied. "
                "Causal decomposition is unavailable, not estimated."
            ),
        )
    total_w = sum(abs(v) for v in lineage.values()) or 1.0
    explained = 0.0
    contrib: dict[str, float] = {}
    rows: list[SecurityContribution] = []
    for name, weight in lineage.items():
        piece = pnl.pnl_total * (weight / total_w)
        contrib[name] = piece
        explained += piece
        rows.append(
            SecurityContribution(
                security_id=name,
                pnl=piece,
                return_contribution=piece / pnl.beginning_equity
                if pnl.beginning_equity
                else 0.0,
            )
        )
    residual = pnl.pnl_total - explained
    return AttributionResult(
        method=AttributionMethod.ESTIMATED,
        total=pnl.pnl_total,
        residual=residual,
        contributions=rows,
        alpha_contributions=contrib,
        status=CheckResult.PASS,
        note="Estimated lineage split. Not exact accounting attribution.",
    )
