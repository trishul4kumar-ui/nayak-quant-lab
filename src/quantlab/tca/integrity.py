"""TCA leak flags. PASS/FAIL lives in quantlab.research.integrity."""

from __future__ import annotations

from pydantic import BaseModel


class TCALeakFlags(BaseModel):
    future_tca_observation: bool | None = None
    future_impact_calibration: bool | None = None
    future_spread_calibration: bool | None = None
    future_volume_calibration: bool | None = None
    future_liquidity_calibration: bool | None = None
    future_capacity_parameter: bool | None = None
    arrival_price_lookahead: bool | None = None
    benchmark_price_lookahead: bool | None = None
    wrong_side_slippage: bool | None = None
    wrong_side_impact: bool | None = None
    posthoc_cost_model: bool | None = None
    model_replay_leak: bool | None = None
    calibration_window_leak: bool | None = None
    future_fill_observation: bool | None = None
    hidden_partial_fill: bool | None = None
    capacity_lookahead: bool | None = None
    synthetic_adv_claim: bool | None = None
    observed_vs_modelled_confusion: bool | None = None
    tca_parameter_mutation: bool | None = None
