"""Slippage/impact remain Prompt 13/18. Shadow does not invent a second model."""

from __future__ import annotations

from quantlab.paper_oms.models import TCAReport
from quantlab.shadow.models import ShadowFill


def modelled_costs(fills: list[ShadowFill], paper_tca: TCAReport | None) -> dict[str, float]:
    spread = sum(item.spread_cost for item in fills)
    slip = sum(item.slippage_cost for item in fills)
    impact = sum(item.impact_cost for item in fills)
    commission = sum(item.commission for item in fills)
    payload = {
        "spread": spread,
        "slippage": slip,
        "impact": impact,
        "commission": commission,
        "kind": 0.0,
    }
    if paper_tca is not None:
        payload["paper_spread"] = paper_tca.spread_drag
        payload["paper_slippage"] = paper_tca.slippage_drag
        payload["paper_impact"] = paper_tca.impact_drag
    return payload
