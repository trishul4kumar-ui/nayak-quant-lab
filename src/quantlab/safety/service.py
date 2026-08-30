"""Safety gateway service. Evaluates live-boundary requests. Never routes."""

from __future__ import annotations

from datetime import UTC, datetime

from quantlab.core.config import LiveSafetyGates
from quantlab.data.fabric.checksums import sha256_bytes
from quantlab.safety.audit import record as record_audit
from quantlab.safety.audit import reset_for_tests as reset_audit
from quantlab.safety.authorization import mint, still_valid
from quantlab.safety.emergency import enter as enter_emergency
from quantlab.safety.errors import AuthorizationError, InvalidSafetyTransition, ReleaseBlocked
from quantlab.safety.gates import evaluate_gates
from quantlab.safety.human_authorization import record as record_human
from quantlab.safety.human_authorization import reset_for_tests as reset_human
from quantlab.safety.idempotency import lookup, remember
from quantlab.safety.idempotency import reset_for_tests as reset_idem
from quantlab.safety.kill_switch import activate, deactivate
from quantlab.safety.kill_switch import reset_for_tests as reset_kills
from quantlab.safety.models import (
    ActorKind,
    HumanApproval,
    KillScope,
    SafetyIncident,
    SafetyRequest,
    SafetyResult,
)
from quantlab.safety.repository import last, list_results, put
from quantlab.safety.repository import reset_for_tests as reset_repo
from quantlab.safety.state import SafetyState, current, force, transition
from quantlab.safety.state import reset_for_tests as reset_state


def reset_for_tests() -> None:
    reset_state()
    reset_kills()
    reset_idem()
    reset_repo()
    reset_audit()
    reset_human()


def _hash(result: SafetyResult) -> str:
    material = (
        f"{result.evaluation_id}|{result.state.value}|"
        + "|".join(f"{g.gate_id.value}:{g.verdict.value}" for g in result.gates)
        + f"|{result.live_release_authorized}"
    )
    return sha256_bytes(material.encode())


def evaluate_request(request: SafetyRequest | None = None) -> SafetyResult:
    request = request or SafetyRequest()
    gates = LiveSafetyGates()
    rows = evaluate_gates(request)
    blocked = any(item.blocks_release for item in rows) or True
    live_ok = False
    incidents: list[SafetyIncident] = []
    if request.live_release:
        incidents.append(
            SafetyIncident(
                incident_id="inc-live-release",
                kind="unauthorized_release",
                detail="live release requested while LIVE_TRADING=false",
                timestamp=request.as_of,
            )
        )
    if request.ai_override:
        incidents.append(
            SafetyIncident(
                incident_id="inc-ai",
                kind="ai_safety_override",
                detail="AI attempted to override safety",
                timestamp=request.as_of,
            )
        )
    replay = lookup(request)
    if replay and replay != "__collision__":
        existing = next(
            (item for item in list_results() if item.evaluation_id == replay),
            None,
        )
        if existing is not None:
            return existing
    evaluation_id = f"saf-{request.request_id}-{request.nonce}"
    result = SafetyResult(
        evaluation_id=evaluation_id,
        state=current(),
        gates=rows,
        live_trading=gates.live_trading,
        live_release_authorized=live_ok,
        broker_routing_enabled=False,
        blocked=blocked,
        incidents=tuple(incidents),
        extras={
            "request_id": request.request_id,
            "idempotency_key": request.idempotency_key,
            "decision_hash": request.decision_hash,
        },
    )
    result = result.model_copy(update={"result_hash": _hash(result)})
    put(result)
    remember(request, result)
    record_audit(result)
    return result


def evaluate_release(request: SafetyRequest | None = None) -> SafetyResult:
    return evaluate_request(request)


def authorize(request: SafetyRequest | None = None) -> SafetyResult:
    request = request or SafetyRequest()
    if request.live_release or LiveSafetyGates().live_trading:
        raise ReleaseBlocked("LIVE_TRADING=false cannot authorize live release")
    if request.ai_override or request.actor is ActorKind.AI_SUGGESTION:
        raise ReleaseBlocked("AI cannot authorize")
    result = evaluate_request(request)
    if request.mutated_target or request.mutated_decision or request.mutated_order_plan:
        raise AuthorizationError("mutated inputs invalidate authorization")
    if request.mutated_authorization:
        raise AuthorizationError("stale or mutated authorization")
    auth = mint(request, authorization_id=f"auth-{request.request_id}")
    if not still_valid(auth, request):
        raise AuthorizationError("stale authorization")
    updated = result.model_copy(
        update={
            "authorization": auth,
            "live_release_authorized": False,
            "blocked": True,
            "note": "Non-live authorization object only. G15 remains BLOCK.",
        }
    )
    updated = updated.model_copy(update={"result_hash": _hash(updated)})
    put(updated)
    return updated


def reject(request: SafetyRequest | None = None, *, reason: str = "rejected") -> SafetyResult:
    request = request or SafetyRequest()
    result = evaluate_request(request)
    incident = SafetyIncident(
        incident_id="inc-reject",
        kind="rejected",
        detail=reason,
        timestamp=request.as_of,
    )
    updated = result.model_copy(update={"incidents": (*result.incidents, incident)})
    put(updated)
    return updated


def kill(scope: KillScope = KillScope.GLOBAL, *, reason: str = "halt") -> SafetyResult:
    activate(scope, reason=reason)
    if current() not in {SafetyState.HALTED, SafetyState.EMERGENCY}:
        try:
            transition(SafetyState.HALTED)
        except InvalidSafetyTransition:
            force(SafetyState.HALTED)
    return evaluate_request()


def unkill(scope: KillScope = KillScope.GLOBAL, *, reason: str = "explicit unkill") -> SafetyResult:
    deactivate(scope, reason=reason)
    return evaluate_request()


def halt(*, reason: str = "operator halt") -> SafetyResult:
    return kill(KillScope.NEW_ORDER, reason=reason)


def emergency(*, reason: str = "emergency") -> SafetyResult:
    enter_emergency(reason=reason)
    activate(KillScope.GLOBAL, reason=reason)
    return evaluate_request()


def recover(*, reason: str = "explicit recovery") -> SafetyResult:
    del reason
    if current() not in {SafetyState.HALTED, SafetyState.EMERGENCY, SafetyState.RECOVERY_PENDING}:
        raise InvalidSafetyTransition(f"{current().value} cannot recover")
    if current() is not SafetyState.RECOVERY_PENDING:
        transition(SafetyState.RECOVERY_PENDING)
    transition(SafetyState.SHADOW)
    return evaluate_request()


def approve_human(*, approval_id: str, reason: str) -> HumanApproval:
    return record_human(
        HumanApproval(
            approval_id=approval_id,
            actor=ActorKind.HUMAN,
            reason=reason,
            timestamp=datetime(2024, 1, 2, tzinfo=UTC),
        )
    )


def last_result() -> SafetyResult | None:
    return last()
