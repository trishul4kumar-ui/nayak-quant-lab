"""Deterministic pre-simulation risk filter for intraday research."""

from dataclasses import dataclass

from quantlab.intraday_research.models import ArrivalState, MicrostructureSnapshot


@dataclass(frozen=True)
class FastRiskPolicy:
    maximum_spread_bps: float
    minimum_top_depth: float
    maximum_actions_per_interval: int
    kill_state: bool = False


def allows(
    snapshot: MicrostructureSnapshot,
    *,
    top_depth: float,
    actions_this_interval: int,
    policy: FastRiskPolicy,
) -> bool:
    if policy.kill_state or snapshot.quality is not ArrivalState.VALID:
        return False
    if (
        snapshot.relative_spread_bps is None
        or snapshot.relative_spread_bps > policy.maximum_spread_bps
    ):
        return False
    if top_depth < policy.minimum_top_depth:
        return False
    return actions_this_interval < policy.maximum_actions_per_interval
