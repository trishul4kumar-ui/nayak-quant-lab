"""Execution fragility and Monte Carlo diagnostics. Not a confidence interval."""

from __future__ import annotations

import random

from pydantic import BaseModel

from quantlab.core.identifiers import InstrumentId
from quantlab.domain.models import OHLCVBar
from quantlab.execution_research.definition import (
    ExecutionFragility,
    MarketMicrostructureDefinition,
)
from quantlab.execution_research.simulator import simulate_execution


class MonteCarloReport(BaseModel):
    schema_version: str = "1"
    n_paths: int
    seed: int
    mean_net: float | None = None
    median_net: float | None = None
    p5: float | None = None
    p25: float | None = None
    p75: float | None = None
    p95: float | None = None
    prob_net_negative: float | None = None
    note: str = (
        "Simulation distribution of execution uncertainty, not a statistical CI "
        "and not alpha significance."
    )


def fragility_score(
    *,
    base_cost: float,
    stress_cost: float,
    fill_ratio: float,
    latency_sessions: int,
) -> ExecutionFragility:
    cost_ratio = 0.0 if base_cost <= 1e-12 else max(stress_cost - base_cost, 0.0) / base_cost
    score = 0.4 * min(cost_ratio, 1.0) + 0.3 * (1.0 - min(max(fill_ratio, 0.0), 1.0))
    score += 0.3 * min(max(latency_sessions, 0) / 5.0, 1.0)
    score = min(max(score, 0.0), 1.0)
    flags: list[str] = []
    if cost_ratio > 0.5:
        flags.append("cost_stress")
    if fill_ratio < 0.8:
        flags.append("incomplete_fill")
    if latency_sessions > 0:
        flags.append("latency")
    return ExecutionFragility(score=score, flags=flags)


def monte_carlo_execution(
    definition: MarketMicrostructureDefinition,
    bars: dict[InstrumentId, list[OHLCVBar]],
    *,
    gross_return: float,
    capital: float = 1_000_000.0,
    n_paths: int = 5,
    seed: int = 0,
) -> MonteCarloReport:
    rng = random.Random(seed)
    nets: list[float] = []
    for _ in range(n_paths):
        slip = definition.slippage_bps * (0.8 + 0.4 * rng.random())
        spread = definition.spread_bps * (0.8 + 0.4 * rng.random())
        model = definition.model_copy(update={"slippage_bps": slip, "spread_bps": spread})
        sim = simulate_execution(model, bars, capital=capital)
        drag = 0.0 if capital <= 0 else sim.total_cost / capital
        nets.append(gross_return - drag)
    ordered = sorted(nets)
    return MonteCarloReport(
        n_paths=n_paths,
        seed=seed,
        mean_net=sum(ordered) / len(ordered),
        median_net=_quantile(ordered, 0.5),
        p5=_quantile(ordered, 0.05),
        p25=_quantile(ordered, 0.25),
        p75=_quantile(ordered, 0.75),
        p95=_quantile(ordered, 0.95),
        prob_net_negative=sum(1 for v in ordered if v < 0) / len(ordered),
    )


def _quantile(ordered: list[float], q: float) -> float:
    if not ordered:
        return 0.0
    idx = min(max(int(q * (len(ordered) - 1)), 0), len(ordered) - 1)
    return ordered[idx]
