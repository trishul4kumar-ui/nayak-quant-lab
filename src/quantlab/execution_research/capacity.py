"""Capacity scenarios. Inputs, not claims. Synthetic volume ≠ NSE ADV."""

from __future__ import annotations

from pydantic import BaseModel, Field

from quantlab.core.identifiers import InstrumentId
from quantlab.domain.models import OHLCVBar
from quantlab.execution_research.definition import MarketMicrostructureDefinition
from quantlab.execution_research.simulator import SimulationResult, simulate_execution

CAPACITY_NOTIONALS: tuple[float, ...] = (
    100_000.0,
    1_000_000.0,
    5_000_000.0,
    10_000_000.0,
    50_000_000.0,
    100_000_000.0,
)


class CapacityRow(BaseModel):
    capital: float
    total_cost: float
    mean_fill_ratio: float
    mean_participation: float | None
    n_partial: int
    n_unfilled: int
    cost_bps_of_capital: float
    note: str = "synthetic volume; capacity remains NOT_TESTED vs official ADV"


class CapacityReport(BaseModel):
    schema_version: str = "1"
    rows: list[CapacityRow] = Field(default_factory=list)
    status: str = "not_tested"
    note: str = (
        "₹1L–₹10Cr notional scenarios on synthetic volume. "
        "Breaks in fill ratio / participation / cost are diagnostics, not NSE capacity."
    )


def capacity_analysis(
    definition: MarketMicrostructureDefinition,
    bars: dict[InstrumentId, list[OHLCVBar]],
    *,
    notionals: tuple[float, ...] = CAPACITY_NOTIONALS,
    lookback: int = 20,
) -> CapacityReport:
    rows: list[CapacityRow] = []
    for capital in notionals:
        sim = simulate_execution(definition, bars, capital=capital, lookback=lookback)
        rows.append(_row(sim, capital))
    return CapacityReport(rows=rows)


def _row(sim: SimulationResult, capital: float) -> CapacityRow:
    bps = 0.0 if capital <= 0 else 10_000.0 * sim.total_cost / capital
    return CapacityRow(
        capital=capital,
        total_cost=sim.total_cost,
        mean_fill_ratio=sim.mean_fill_ratio,
        mean_participation=sim.mean_participation,
        n_partial=sim.n_partial,
        n_unfilled=sim.n_unfilled,
        cost_bps_of_capital=bps,
    )
