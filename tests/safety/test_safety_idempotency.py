from __future__ import annotations

from quantlab.safety.gate_results import GateVerdict
from quantlab.safety.models import SafetyRequest
from quantlab.safety.service import evaluate_request


def test_duplicate_request_is_idempotent() -> None:
    first = evaluate_request(SafetyRequest(idempotency_key="k1", nonce="n1"))
    second = evaluate_request(SafetyRequest(idempotency_key="k1", nonce="n1"))
    assert first.evaluation_id == second.evaluation_id
    assert first.result_hash == second.result_hash


def test_conflicting_idempotency_key_is_rejected() -> None:
    evaluate_request(SafetyRequest(idempotency_key="k2", nonce="n1", decision_hash="a"))
    result = evaluate_request(SafetyRequest(idempotency_key="k2", nonce="n2", decision_hash="b"))
    assert result.gate("G11_IDEMPOTENCY").verdict is GateVerdict.BLOCK
