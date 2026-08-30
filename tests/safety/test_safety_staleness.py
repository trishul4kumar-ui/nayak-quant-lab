from __future__ import annotations

from quantlab.safety.gate_results import GateVerdict
from quantlab.safety.models import SafetyRequest
from quantlab.safety.service import evaluate_request


def test_stale_decision_blocks() -> None:
    result = evaluate_request(SafetyRequest(decision_age_ms=1_000_000, max_age_ms=10))
    assert result.gate("G8_STALENESS").verdict is GateVerdict.BLOCK


def test_stale_authorization_blocks() -> None:
    result = evaluate_request(SafetyRequest(authorization_age_ms=1_000_000, max_age_ms=10))
    assert result.gate("G8_STALENESS").verdict is GateVerdict.BLOCK
