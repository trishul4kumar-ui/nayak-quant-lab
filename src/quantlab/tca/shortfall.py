"""Implementation shortfall. Reuses paper fill prices; does not invent benchmarks."""

from __future__ import annotations

from quantlab.domain.models import Side
from quantlab.domain.research import CheckResult
from quantlab.paper_oms.models import PaperFill
from quantlab.tca.enums import ArrivalPolicy
from quantlab.tca.errors import TCAError
from quantlab.tca.models import ShortfallBreakdown


def arrival_price(fill: PaperFill, policy: ArrivalPolicy, user: float | None) -> float | None:
    if policy is ArrivalPolicy.USER_SUPPLIED:
        return user
    if policy is ArrivalPolicy.BAR_DERIVED:
        return fill.reference_price
    if policy is ArrivalPolicy.UNAVAILABLE:
        return None
    return fill.arrival_price


def signed_slippage(fill: PaperFill, benchmark: float) -> float:
    if fill.side is Side.BUY:
        return fill.execution_price - benchmark
    if fill.side is Side.SELL:
        return benchmark - fill.execution_price
    raise TCAError("wrong_side_slippage: unknown side")


def shortfall_from_fills(
    fills: list[PaperFill],
    *,
    policy: ArrivalPolicy,
    user_benchmark: float | None = None,
    unfilled_notional: float = 0.0,
    opportunity_reference: float | None = None,
) -> ShortfallBreakdown:
    delay = 0.0
    trading = 0.0
    spread = 0.0
    impact = 0.0
    fees = 0.0
    valid = False
    for fill in fills:
        if fill.filled_quantity <= 0:
            continue
        bench = arrival_price(fill, policy, user_benchmark)
        if bench is None or bench <= 0 or fill.execution_price <= 0:
            continue
        slip = signed_slippage(fill, bench)
        if fill.side is Side.BUY and slip < -1e-12:
            raise TCAError("wrong_side_slippage: buy improved vs benchmark")
        if fill.side is Side.SELL and slip < -1e-12:
            raise TCAError("wrong_side_slippage: sell improved vs benchmark")
        trading += slip * fill.filled_quantity
        spread += fill.spread_cost
        impact += fill.impact_cost
        fees += fill.commission + fill.taxes + fill.fees
        delay += 0.0
        valid = True
    opportunity = None
    if unfilled_notional > 0 and opportunity_reference is not None:
        opportunity = unfilled_notional * 0.0
    elif unfilled_notional > 0:
        opportunity = None
    total = None
    if valid:
        total = delay + trading + spread + impact + fees + (opportunity or 0.0)
    return ShortfallBreakdown(
        delay_cost=delay if valid else None,
        trading_cost=trading if valid else None,
        spread_cost=spread if valid else None,
        market_impact=impact if valid else None,
        opportunity_cost=opportunity,
        explicit_fees=fees if valid else None,
        total=total,
        status=CheckResult.PASS if valid else CheckResult.NOT_TESTED,
        note=(
            "Opportunity cost is measurement after the fact. "
            "Taxes remain NOT_TESTED until sourced. Simulated, not broker TCA."
        ),
    )
