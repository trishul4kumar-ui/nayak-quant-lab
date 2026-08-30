from __future__ import annotations

import pytest

from quantlab.safety.gate_results import GateVerdict
from quantlab.safety.models import ReconStatus, SafetyRequest
from quantlab.safety.service import evaluate_request


@pytest.mark.parametrize(
    ("payload", "gate_id"),
    [
        (SafetyRequest(certification_id="", certification_expired=False), "G2_CERTIFICATION"),
        (SafetyRequest(certification_expired=True, certification_id="c1"), "G2_CERTIFICATION"),
        (SafetyRequest(research_gate_failed=True), "G1_RESEARCH_INTEGRITY"),
        (SafetyRequest(recon_status=ReconStatus.MISMATCH), "G9_RECONCILIATION"),
        (SafetyRequest(risk_unknown=True), "G6_RISK"),
        (SafetyRequest(decision_age_ms=999_999, max_age_ms=1), "G8_STALENESS"),
        (SafetyRequest(live_release=True), "G0_LIVE_MODE"),
    ],
)
def test_blocking_gates(payload: SafetyRequest, gate_id: str) -> None:
    result = evaluate_request(payload)
    gate = result.gate(gate_id)
    assert gate is not None
    assert gate.blocks_release
    assert result.live_release_authorized is False
    g15 = result.gate("G15_FINAL_RELEASE")
    assert g15 is not None
    assert g15.verdict is GateVerdict.BLOCK


def test_missing_certification_is_not_tested() -> None:
    result = evaluate_request(SafetyRequest(certification_id=""))
    gate = result.gate("G2_CERTIFICATION")
    assert gate is not None
    assert gate.verdict is GateVerdict.NOT_TESTED


def test_unknown_never_pass() -> None:
    result = evaluate_request(SafetyRequest(risk_unknown=True, recon_status=ReconStatus.UNKNOWN))
    assert result.gate("G6_RISK") is not None
    assert result.gate("G6_RISK").verdict is GateVerdict.NOT_TESTED
    assert result.gate("G9_RECONCILIATION").verdict is GateVerdict.BLOCK
