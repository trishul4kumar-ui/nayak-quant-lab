"""Liquidity-aware allocation. Unknown is not infinite. ADV is never invented."""

from __future__ import annotations

from quantlab.capital.definitions import LiquidityPolicy, LiquidityStatus


def classify_name(
    adv: float | None,
    notional: float,
    policy: LiquidityPolicy,
) -> LiquidityStatus:
    if adv is None:
        return LiquidityStatus.UNKNOWN
    if adv <= 0:
        return LiquidityStatus.UNKNOWN
    if abs(notional) > policy.participation_limit * adv:
        return LiquidityStatus.INSUFFICIENT
    return LiquidityStatus.KNOWN


def portfolio_liquidity(
    notionals: dict[str, float],
    adv: dict[str, float | None],
    policy: LiquidityPolicy,
) -> tuple[LiquidityStatus, dict[str, LiquidityStatus]]:
    per: dict[str, LiquidityStatus] = {}
    unknown = False
    insufficient = False
    known = False
    for name in sorted(notionals):
        status = classify_name(adv.get(name), notionals[name], policy)
        per[name] = status
        if status is LiquidityStatus.UNKNOWN:
            unknown = True
        elif status is LiquidityStatus.INSUFFICIENT:
            insufficient = True
        else:
            known = True
    if insufficient:
        return LiquidityStatus.INSUFFICIENT, per
    if unknown and not known:
        return LiquidityStatus.UNKNOWN, per
    if unknown:
        return LiquidityStatus.UNKNOWN, per
    return LiquidityStatus.KNOWN, per
