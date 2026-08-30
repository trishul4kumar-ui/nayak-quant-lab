"""Emergency mode. Strategy cannot override. No auto-recovery to AUTHORIZED."""

from __future__ import annotations

from quantlab.safety.gate_results import GateId, GateResult, GateVerdict
from quantlab.safety.state import SafetyState, current, transition


def enter(*, reason: str) -> SafetyState:
    del reason
    return transition(SafetyState.EMERGENCY)


def check_emergency() -> GateResult:
    if current() is SafetyState.EMERGENCY:
        return GateResult(
            gate_id=GateId.G14_EMERGENCY,
            verdict=GateVerdict.EMERGENCY,
            reason="emergency mode; strategy cannot override",
        )
    return GateResult(
        gate_id=GateId.G14_EMERGENCY,
        verdict=GateVerdict.PASS,
        reason="not in emergency",
        critical=False,
    )
