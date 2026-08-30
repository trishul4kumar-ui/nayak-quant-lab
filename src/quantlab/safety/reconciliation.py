"""Reconciliation is a hard barrier. No auto-repair."""

from __future__ import annotations

from quantlab.safety.gate_results import GateId, GateResult, GateVerdict
from quantlab.safety.models import ReconStatus, SafetyRequest


def check_reconciliation(request: SafetyRequest) -> GateResult:
    if request.recon_status in {
        ReconStatus.MISMATCH,
        ReconStatus.UNKNOWN,
        ReconStatus.EMERGENCY,
    }:
        return GateResult(
            gate_id=GateId.G9_RECONCILIATION,
            verdict=GateVerdict.BLOCK,
            reason=f"reconciliation {request.recon_status.value}",
        )
    if request.recon_status is ReconStatus.PENDING:
        return GateResult(
            gate_id=GateId.G9_RECONCILIATION,
            verdict=GateVerdict.BLOCK,
            reason="previous state unreconciled",
        )
    return GateResult(
        gate_id=GateId.G9_RECONCILIATION,
        verdict=GateVerdict.PASS,
        reason="reconciled (not a broker confirmation)",
    )
