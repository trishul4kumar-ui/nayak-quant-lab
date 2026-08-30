from __future__ import annotations

from quantlab.safety.gate_results import GateVerdict
from quantlab.safety.models import ReconStatus, SafetyRequest
from quantlab.safety.service import evaluate_request


def test_failed_reconciliation_blocks() -> None:
    result = evaluate_request(SafetyRequest(recon_status=ReconStatus.MISMATCH))
    assert result.gate("G9_RECONCILIATION").verdict is GateVerdict.BLOCK
    assert result.live_release_authorized is False
