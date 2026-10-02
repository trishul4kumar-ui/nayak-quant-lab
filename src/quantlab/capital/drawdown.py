"""Drawdown capital-state machine. Thresholds come from policy, not engine constants."""

from __future__ import annotations

from quantlab.capital.definitions import (
    AllocationMultipliers,
    CapitalAllocationState,
    DrawdownLimits,
    DrawdownState,
)


def classify_drawdown(drawdown: float, limits: DrawdownLimits) -> DrawdownState:
    dd = abs(drawdown)
    if dd >= limits.halt:
        return DrawdownState.HALTED
    if dd >= limits.defensive:
        return DrawdownState.DEFENSIVE
    if dd >= limits.caution:
        return DrawdownState.CAUTION
    return DrawdownState.NORMAL


def allocation_state(drawdown_state: DrawdownState) -> CapitalAllocationState:
    mapping = {
        DrawdownState.NORMAL: CapitalAllocationState.FULL,
        DrawdownState.CAUTION: CapitalAllocationState.REDUCED,
        DrawdownState.DEFENSIVE: CapitalAllocationState.DEFENSIVE,
        DrawdownState.HALTED: CapitalAllocationState.HALT,
    }
    return mapping[drawdown_state]


def multiplier(state: CapitalAllocationState, multipliers: AllocationMultipliers) -> float:
    return {
        CapitalAllocationState.FULL: multipliers.full,
        CapitalAllocationState.REDUCED: multipliers.reduced,
        CapitalAllocationState.DEFENSIVE: multipliers.defensive,
        CapitalAllocationState.ABSTAIN: multipliers.abstain,
        CapitalAllocationState.HALT: multipliers.halt,
    }[state]


def scale_weights(weights: dict[str, float], factor: float) -> dict[str, float]:
    return {name: weights[name] * factor for name in sorted(weights)}
