from __future__ import annotations

from quantlab.safety.gate_results import GateVerdict
from quantlab.safety.models import SafetyRequest
from quantlab.safety.service import emergency, evaluate_request
from quantlab.safety.state import SafetyState, current


def test_emergency_blocks() -> None:
    emergency(reason="test")
    assert current() is SafetyState.EMERGENCY
    result = evaluate_request(SafetyRequest())
    assert result.gate("G14_EMERGENCY").verdict is GateVerdict.EMERGENCY
    assert result.live_release_authorized is False
