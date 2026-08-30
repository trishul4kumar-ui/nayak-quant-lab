"""Execution sensitivity. Diagnostic, not an optimizer."""

from __future__ import annotations

from pydantic import BaseModel, Field

from quantlab.core.identifiers import InstrumentId
from quantlab.domain.models import OHLCVBar
from quantlab.execution_research.definition import MarketMicrostructureDefinition
from quantlab.execution_research.simulator import simulate_execution

SPREAD_GRID = (0.0, 5.0, 10.0, 25.0, 50.0)
SLIP_GRID = (0.0, 2.0, 5.0, 10.0, 20.0)
PART_GRID = (0.05, 0.10, 0.20, 0.30)


class SensitivityRow(BaseModel):
    name: str
    value: float
    total_cost: float
    mean_fill_ratio: float
    n_partial: int


class SensitivityReport(BaseModel):
    schema_version: str = "1"
    spread: list[SensitivityRow] = Field(default_factory=list)
    slippage: list[SensitivityRow] = Field(default_factory=list)
    participation: list[SensitivityRow] = Field(default_factory=list)
    note: str = "Sensitivity is a diagnostic grid, not parameter search for promotion."


def sensitivity_report(
    definition: MarketMicrostructureDefinition,
    bars: dict[InstrumentId, list[OHLCVBar]],
    *,
    capital: float = 1_000_000.0,
) -> SensitivityReport:
    spread_rows = [
        _run(definition.model_copy(update={"spread_bps": v}), bars, capital, "spread_bps", v)
        for v in SPREAD_GRID
    ]
    slip_rows = [
        _run(definition.model_copy(update={"slippage_bps": v}), bars, capital, "slippage_bps", v)
        for v in SLIP_GRID
    ]
    part_rows = [
        _run(
            definition.model_copy(update={"max_participation": v}),
            bars,
            capital,
            "max_participation",
            v,
        )
        for v in PART_GRID
    ]
    return SensitivityReport(spread=spread_rows, slippage=slip_rows, participation=part_rows)


def _run(
    model: MarketMicrostructureDefinition,
    bars: dict[InstrumentId, list[OHLCVBar]],
    capital: float,
    name: str,
    value: float,
) -> SensitivityRow:
    sim = simulate_execution(model, bars, capital=capital)
    return SensitivityRow(
        name=name,
        value=value,
        total_cost=sim.total_cost,
        mean_fill_ratio=sim.mean_fill_ratio,
        n_partial=sim.n_partial,
    )
