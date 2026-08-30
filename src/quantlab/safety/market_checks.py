"""Market-snapshot safety. Latest price is not used merely because it exists."""

from __future__ import annotations

from quantlab.safety.gate_results import GateId, GateResult, GateVerdict
from quantlab.safety.models import SafetyRequest


def check_market(request: SafetyRequest) -> GateResult:
    if request.future_market:
        return GateResult(
            gate_id=GateId.G4_MARKET_DATA,
            verdict=GateVerdict.BLOCK,
            reason="future market state",
        )
    if not request.market_snapshot_hash:
        return GateResult(
            gate_id=GateId.G4_MARKET_DATA,
            verdict=GateVerdict.NOT_TESTED,
            reason="required market snapshot unavailable",
        )
    return GateResult(
        gate_id=GateId.G4_MARKET_DATA,
        verdict=GateVerdict.PASS,
        reason="snapshot identity present (not a live quote)",
        critical=False,
    )
