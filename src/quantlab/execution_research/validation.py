"""Detect execution-integrity conditions from a simulation. Missing ≠ PASS."""

from __future__ import annotations

from quantlab.execution_research.definition import (
    ExecutionLeakFlags,
    FillKind,
    ImpactKind,
    MarketMicrostructureDefinition,
    SlippageKind,
)
from quantlab.execution_research.simulator import SimulationResult


def zero_cost_execution(definition: MarketMicrostructureDefinition, sim: SimulationResult) -> bool:
    explicit = definition.cost.total_bps()
    no_impact = definition.impact_model is ImpactKind.NONE or (
        definition.impact_bps <= 0 and definition.impact_k <= 0
    )
    no_slip = definition.slippage_model is SlippageKind.NONE or definition.slippage_bps <= 0
    return (
        definition.spread_bps <= 0
        and no_slip
        and no_impact
        and explicit <= 0
        and sim.total_cost <= 1e-12
    )


def full_fill_assumption(
    definition: MarketMicrostructureDefinition, flags: ExecutionLeakFlags
) -> bool:
    return flags.full_fill or definition.fill_model is FillKind.FULL


def wrong_side_from_fills(sim: SimulationResult) -> tuple[bool, bool]:
    slip = False
    impact = False
    for fill in sim.fills:
        if fill.quantity <= 0:
            continue
        if fill.side.value == "buy":
            if fill.slippage_bps < 0:
                slip = True
            if fill.impact_bps < 0:
                impact = True
        else:
            if fill.slippage_bps < 0:
                slip = True
            if fill.impact_bps < 0:
                impact = True
    return slip, impact


def hidden_partial(sim: SimulationResult) -> bool:
    return any(
        fill.fill_status.value == "fully_filled" and fill.remaining_quantity > 1e-12
        for fill in sim.fills
    )
