"""Abstention is a first-class capital decision."""

from __future__ import annotations

from quantlab.capital.definitions import AbstentionCode, DecisionStatus


def status_for_code(code: AbstentionCode) -> DecisionStatus:
    if code is AbstentionCode.NONE:
        return DecisionStatus.ALLOCATED
    if code is AbstentionCode.GATE_FAIL:
        return DecisionStatus.REJECTED
    if code is AbstentionCode.SYNTHETIC_RESEARCH_ONLY:
        return DecisionStatus.RESEARCH_ONLY
    if code is AbstentionCode.LIVE_PATH_CLOSED:
        return DecisionStatus.REJECTED
    return DecisionStatus.ABSTAIN


def reason_for(code: AbstentionCode, detail: str = "") -> str:
    base = {
        AbstentionCode.NONE: "allocation proceeded",
        AbstentionCode.GATE_FAIL: "research gate prohibited allocation",
        AbstentionCode.PIT_INTEGRITY_FAIL: "PIT integrity failed",
        AbstentionCode.RISK_UNAVAILABLE: "risk estimate unavailable",
        AbstentionCode.COVARIANCE_INVALID: "covariance missing or invalid",
        AbstentionCode.UNKNOWN_LIQUIDITY: "liquidity unknown under strict policy",
        AbstentionCode.UNKNOWN_FACTOR: "factor exposure unknown under strict policy",
        AbstentionCode.EXPECTED_RETURN_UNAVAILABLE: "expected return unavailable",
        AbstentionCode.CONFIDENCE_BELOW_THRESHOLD: "allocation confidence below threshold",
        AbstentionCode.DRAWDOWN_HALT: "drawdown state is HALTED; no new exposure",
        AbstentionCode.CONSTRAINT_INFEASIBLE: "hard constraints infeasible",
        AbstentionCode.EXECUTION_DRAG: "execution drag overwhelms expected edge",
        AbstentionCode.DATA_QUALITY: "data quality insufficient",
        AbstentionCode.MODEL_STABILITY: "model stability fails",
        AbstentionCode.KELLY_UNRELIABLE: "Kelly inputs unreliable",
        AbstentionCode.TARGET_UNACHIEVABLE: "volatility target unachievable within leverage",
        AbstentionCode.CAPITAL_INSUFFICIENT: "investable capital is non-positive",
        AbstentionCode.LIVE_PATH_CLOSED: "live trading path is closed",
        AbstentionCode.SYNTHETIC_RESEARCH_ONLY: "synthetic data remains research diagnostics",
    }[code]
    return f"{base}: {detail}" if detail else base
