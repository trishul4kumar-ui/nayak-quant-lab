"""Cost and alpha-to-execution attribution."""

from __future__ import annotations

from collections import defaultdict

from pydantic import BaseModel, Field

from quantlab.execution_research.simulator import SimulationResult


class CostAttribution(BaseModel):
    schema_version: str = "1"
    spread: float = 0.0
    slippage: float = 0.0
    impact: float = 0.0
    explicit: float = 0.0
    total: float = 0.0
    by_side: dict[str, float] = Field(default_factory=dict)
    by_name: dict[str, float] = Field(default_factory=dict)
    dominant: str = "none"
    note: str = "Components are simulated drag, not guaranteed broker costs."


class AlphaExecutionAttribution(BaseModel):
    schema_version: str = "1"
    gross_edge: float | None = None
    execution_drag: float = 0.0
    net_edge: float | None = None
    survived: bool | None = None
    note: str = (
        "Gross uses the canonical next-bar engine at 0 cost as GROSS_EDGE isolation. "
        "That path is unrealistic. Net overlays decomposed execution costs."
    )


def cost_attribution(sim: SimulationResult) -> CostAttribution:
    by_side: dict[str, float] = defaultdict(float)
    by_name: dict[str, float] = defaultdict(float)
    for fill in sim.fills:
        by_side[fill.side.value] += fill.total_cost
        by_name[fill.security_id] += fill.total_cost
    parts = {
        "spread": sim.spread_cost,
        "slippage": sim.slippage_cost,
        "impact": sim.impact_cost,
        "explicit": sim.explicit_cost,
    }
    dominant = max(parts, key=lambda k: abs(parts[k])) if sim.total_cost else "none"
    return CostAttribution(
        spread=sim.spread_cost,
        slippage=sim.slippage_cost,
        impact=sim.impact_cost,
        explicit=sim.explicit_cost,
        total=sim.total_cost,
        by_side=dict(by_side),
        by_name=dict(by_name),
        dominant=dominant,
    )


def alpha_execution_attribution(
    *,
    gross_return: float | None,
    total_cost: float,
    capital: float,
) -> AlphaExecutionAttribution:
    drag = 0.0 if capital <= 0 else total_cost / capital
    net = None if gross_return is None else gross_return - drag
    survived = None if net is None else net > 0
    return AlphaExecutionAttribution(
        gross_edge=gross_return,
        execution_drag=drag,
        net_edge=net,
        survived=survived,
    )
