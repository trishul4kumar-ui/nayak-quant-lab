"""Econometric leak flags. PASS/FAIL lives in quantlab.research.integrity."""

from __future__ import annotations

from pydantic import BaseModel


class EconometricLeakFlags(BaseModel):
    future_stationarity_window: bool | None = None
    future_lag_selection: bool | None = None
    future_break_detection: bool | None = None
    future_cointegration_selection: bool | None = None
    future_var_selection: bool | None = None
    future_causal_control: bool | None = None
    future_event_window: bool | None = None
    future_parameter_estimation: bool | None = None
    full_sample_econometric_replay: bool | None = None
    future_residual_normalization: bool | None = None
    future_panel_selection: bool | None = None
    causal_post_treatment_control: bool | None = None
    lookahead_event_study: bool | None = None
