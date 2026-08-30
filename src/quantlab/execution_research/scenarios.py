"""Versioned execution scenarios. They are assumptions, not forecasts."""

from __future__ import annotations

from quantlab.execution_research.definition import MarketMicrostructureDefinition
from quantlab.execution_research.registry import get_execution_model

SCENARIO_MODELS: dict[str, str] = {
    "BASE": "exec_base",
    "CONSERVATIVE": "exec_conservative",
    "HIGH_SLIPPAGE": "exec_high_slippage",
    "WIDE_SPREAD": "exec_wide_spread",
    "HIGH_IMPACT": "exec_high_impact",
    "LOW_LIQUIDITY": "exec_low_liquidity",
    "HIGH_LATENCY": "exec_high_latency",
    "PARTIAL_FILL": "exec_partial",
    "STRESSED": "exec_stressed",
    "ZERO_COST": "exec_zero_cost",
}


def scenario_model(scenario_id: str) -> MarketMicrostructureDefinition:
    key = scenario_id.upper()
    model_id = SCENARIO_MODELS.get(key, scenario_id)
    return get_execution_model(model_id)


def list_scenarios() -> list[str]:
    return list(SCENARIO_MODELS)
