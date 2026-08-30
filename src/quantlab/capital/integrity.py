"""Capital leak flags. Actual PASS/FAIL lives in quantlab.research.integrity."""

from __future__ import annotations

from pydantic import BaseModel


class CapitalLeakFlags(BaseModel):
    future_capital_input: bool | None = None
    future_risk_input: bool | None = None
    future_expected_return: bool | None = None
    future_factor_exposure: bool | None = None
    future_liquidity: bool | None = None
    future_turnover_state: bool | None = None
    future_drawdown_state: bool | None = None
    future_constraint_parameter: bool | None = None
    future_position_reference: bool | None = None
    future_decision_state: bool | None = None
    capital_policy_mutation: bool | None = None
    decision_mutation: bool | None = None
    decision_hash_mismatch: bool | None = None
    allocation_lineage_break: bool | None = None
    hidden_constraint_relaxation: bool | None = None
    silent_fallback: bool | None = None
    unknown_liquidity_as_infinite: bool | None = None
    unknown_factor_as_zero: bool | None = None
    synthetic_capital_overpromotion: bool | None = None
    gate_bypass: bool | None = None
    abstention_suppression: bool | None = None
    future_portfolio_state: bool | None = None
    future_execution_cost: bool | None = None
