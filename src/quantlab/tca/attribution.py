"""Cost attribution vs paper OMS TCA. Distinct objects."""

from __future__ import annotations

from quantlab.paper_oms.models import TCAReport
from quantlab.tca.models import ShortfallBreakdown


def compare_paper(paper: TCAReport, tca: ShortfallBreakdown) -> dict[str, float | None]:
    return {
        "paper_shortfall": paper.implementation_shortfall,
        "tca_shortfall": tca.total,
        "spread": tca.spread_cost,
        "impact": tca.market_impact,
    }
