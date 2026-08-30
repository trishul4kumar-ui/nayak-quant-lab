"""Idempotency keys. Identical retries replay. Conflicts reject."""

from __future__ import annotations

from threading import Lock

from quantlab.data.fabric.checksums import sha256_bytes
from quantlab.safety.gate_results import GateId, GateResult, GateVerdict
from quantlab.safety.models import SafetyRequest, SafetyResult

_LOCK = Lock()
_KEYS: dict[str, tuple[str, str]] = {}


def payload_hash(request: SafetyRequest) -> str:
    material = (
        f"{request.decision_hash}|{request.target_portfolio_hash}|"
        f"{request.order_plan_hash}|{request.live_release}|{request.nonce}"
    )
    return sha256_bytes(material.encode())


def reset_for_tests() -> None:
    with _LOCK:
        _KEYS.clear()


def remember(request: SafetyRequest, result: SafetyResult) -> None:
    digest = payload_hash(request)
    with _LOCK:
        _KEYS[request.idempotency_key] = (digest, result.evaluation_id)


def lookup(request: SafetyRequest) -> str | None:
    with _LOCK:
        found = _KEYS.get(request.idempotency_key)
    if found is None:
        return None
    digest, evaluation_id = found
    if digest == payload_hash(request):
        return evaluation_id
    return "__collision__"


def check_idempotency(request: SafetyRequest) -> GateResult:
    found = lookup(request)
    if found == "__collision__":
        return GateResult(
            gate_id=GateId.G11_IDEMPOTENCY,
            verdict=GateVerdict.BLOCK,
            reason="idempotency collision",
        )
    return GateResult(
        gate_id=GateId.G11_IDEMPOTENCY,
        verdict=GateVerdict.PASS,
        reason="idempotency key accepted",
        critical=False,
    )
