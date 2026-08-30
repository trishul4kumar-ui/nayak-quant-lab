"""Reuse Prompt 08/17 risk evidence. Not a second risk engine."""

from __future__ import annotations

from quantlab.safety.gate_results import GateId, GateResult, GateVerdict
from quantlab.safety.models import SafetyRequest


def check_risk(request: SafetyRequest) -> GateResult:
    if request.risk_violation:
        return GateResult(
            gate_id=GateId.G6_RISK,
            verdict=GateVerdict.BLOCK,
            reason="hard risk violation",
        )
    if request.risk_unknown or request.risk_state in {"", "unknown"}:
        return GateResult(
            gate_id=GateId.G6_RISK,
            verdict=GateVerdict.NOT_TESTED,
            reason="unknown risk state blocks live release",
        )
    return GateResult(
        gate_id=GateId.G6_RISK,
        verdict=GateVerdict.PASS,
        reason="risk snapshot present (not live authorization)",
    )
