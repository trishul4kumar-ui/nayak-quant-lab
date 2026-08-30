from __future__ import annotations

from quantlab.safety.gate_results import GateVerdict
from quantlab.safety.models import SafetyRequest
from quantlab.safety.service import evaluate_request


def test_unknown_risk_state_blocks() -> None:
    result = evaluate_request(SafetyRequest(risk_unknown=True, risk_state="unknown"))
    gate = result.gate("G6_RISK")
    assert gate is not None
    assert gate.verdict is GateVerdict.NOT_TESTED
    assert gate.blocks_release


def test_hard_risk_violation_blocks() -> None:
    result = evaluate_request(
        SafetyRequest(risk_unknown=False, risk_state="ok", risk_violation=True)
    )
    assert result.gate("G6_RISK").verdict is GateVerdict.BLOCK
