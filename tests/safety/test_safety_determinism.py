from __future__ import annotations

from quantlab.safety.models import SafetyRequest
from quantlab.safety.service import evaluate_request


def test_identical_inputs_same_hash() -> None:
    payload = SafetyRequest(request_id="det", nonce="same")
    first = evaluate_request(payload)
    second = evaluate_request(payload)
    assert first.result_hash == second.result_hash
    assert first.evaluation_id == second.evaluation_id
