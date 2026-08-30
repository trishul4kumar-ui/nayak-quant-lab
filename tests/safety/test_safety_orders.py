from __future__ import annotations

from quantlab.safety.gate_results import GateVerdict
from quantlab.safety.models import SafetyRequest
from quantlab.safety.service import evaluate_request


def test_negative_quantity_blocks() -> None:
    result = evaluate_request(SafetyRequest(quantity=-1))
    assert result.gate("G7_ORDER_SAFETY").verdict is GateVerdict.BLOCK


def test_invalid_side_blocks() -> None:
    result = evaluate_request(SafetyRequest(side="hold"))
    assert result.gate("G7_ORDER_SAFETY").verdict is GateVerdict.BLOCK
