"""Capacity under an explicit policy. Missing volume → NOT_TESTED, not infinite."""

from __future__ import annotations

from quantlab.tca.enums import CapacityStatus
from quantlab.tca.models import (
    CapacityPolicy,
    CapacityResult,
    CapacityScenario,
    LiquidityObservation,
)

LADDER: tuple[float, ...] = (
    100_000.0,
    500_000.0,
    1_000_000.0,
    2_500_000.0,
    5_000_000.0,
    10_000_000.0,
    50_000_000.0,
    100_000_000.0,
)


def capacity_from_liquidity(
    liquidity: LiquidityObservation,
    policy: CapacityPolicy,
    *,
    turnover: float,
    expected_edge: float | None,
    impact_k: float | None,
) -> CapacityResult:
    if liquidity.volume is None or liquidity.volume <= 0:
        return CapacityResult(
            policy_id=policy.policy_id,
            status=CapacityStatus.NOT_TESTED,
            note="Missing volume. Capacity is NOT_TESTED, not infinite. Not NSE ADV.",
        )
    rows: list[CapacityScenario] = []
    max_ok: float | None = None
    for capital in LADDER:
        order = capital * max(turnover, 0.0)
        part = order / liquidity.volume if liquidity.volume else None
        impact = None
        if part is not None and impact_k is not None:
            impact = impact_k * (max(part, 0.0) ** 0.5) * 10_000.0
        cost = None if impact is None else capital * impact / 10_000.0
        net = None
        if expected_edge is not None and cost is not None:
            net = expected_edge * capital - cost
        breach = False
        if part is not None and part > policy.max_participation:
            breach = True
        if impact is not None and impact > policy.max_cost_bps:
            breach = True
        if net is not None and net < policy.min_net_edge * capital:
            breach = True
        if not breach:
            max_ok = capital
        rows.append(
            CapacityScenario(
                capital=capital,
                participation=part,
                estimated_impact_bps=impact,
                expected_cost=cost,
                net_edge=net,
                turnover=turnover,
                unfilled=None,
                breach=breach,
                note="₹ ladder is a diagnostic, not a claim.",
            )
        )
    status = CapacityStatus.FEASIBLE if max_ok is not None else CapacityStatus.BREACH
    return CapacityResult(
        policy_id=policy.policy_id,
        status=status,
        scenarios=rows,
        max_feasible_capital=max_ok,
        note="Policy-defined capacity. Synthetic volume is not NSE ADV.",
    )
