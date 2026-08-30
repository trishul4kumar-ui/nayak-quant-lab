"""Human authorization boundary. Cannot bypass gates. AI is AI_SUGGESTION."""

from __future__ import annotations

from threading import Lock

from quantlab.safety.gate_results import GateId, GateResult, GateVerdict
from quantlab.safety.models import ActorKind, HumanApproval, SafetyRequest

_LOCK = Lock()
_APPROVALS: dict[str, HumanApproval] = {}


def reset_for_tests() -> None:
    with _LOCK:
        _APPROVALS.clear()


def record(approval: HumanApproval) -> HumanApproval:
    if approval.actor is not ActorKind.HUMAN:
        raise ValueError("only HUMAN may record authorization")
    with _LOCK:
        _APPROVALS[approval.approval_id] = approval
    return approval


def get(approval_id: str) -> HumanApproval | None:
    return _APPROVALS.get(approval_id)


def check_human(request: SafetyRequest) -> GateResult:
    if request.actor is ActorKind.AI_SUGGESTION and request.human_approval_id == "":
        return GateResult(
            gate_id=GateId.G12_HUMAN_AUTH,
            verdict=GateVerdict.BLOCK,
            reason="AI_SUGGESTION cannot authorize",
        )
    if request.human_approval_id:
        approval = get(request.human_approval_id)
        if approval is None:
            return GateResult(
                gate_id=GateId.G12_HUMAN_AUTH,
                verdict=GateVerdict.NOT_TESTED,
                reason="human authorization missing",
            )
        return GateResult(
            gate_id=GateId.G12_HUMAN_AUTH,
            verdict=GateVerdict.PASS,
            reason="human approval recorded; gates still apply",
            critical=False,
        )
    return GateResult(
        gate_id=GateId.G12_HUMAN_AUTH,
        verdict=GateVerdict.NOT_TESTED,
        reason="human authorization missing",
        critical=False,
    )
