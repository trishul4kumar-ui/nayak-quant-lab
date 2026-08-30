"""TTL policies. Expired objects must not be reused."""

from __future__ import annotations

from quantlab.safety.gate_results import GateId, GateResult, GateVerdict
from quantlab.safety.models import SafetyRequest


def check_staleness(request: SafetyRequest) -> GateResult:
    if request.decision_age_ms > request.max_age_ms:
        return GateResult(
            gate_id=GateId.G8_STALENESS,
            verdict=GateVerdict.BLOCK,
            reason="stale decision",
        )
    if request.authorization_age_ms > request.max_age_ms:
        return GateResult(
            gate_id=GateId.G8_STALENESS,
            verdict=GateVerdict.BLOCK,
            reason="stale authorization",
        )
    return GateResult(
        gate_id=GateId.G8_STALENESS,
        verdict=GateVerdict.PASS,
        reason="freshness within policy",
        critical=False,
    )
