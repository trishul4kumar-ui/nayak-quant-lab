"""In-process audit store for gateway state; no broker credentials or payload mutation."""
# ruff: noqa: E501

from __future__ import annotations

from threading import Lock

from quantlab.restricted_execution.models import (
    ExecutionEnvelope,
    GatewaySubmission,
    HumanConfirmation,
)

_LOCK = Lock()
_ENVELOPES: dict[str, ExecutionEnvelope] = {}
_CONFIRMATIONS: dict[str, HumanConfirmation] = {}
_SUBMISSIONS: dict[str, GatewaySubmission] = {}
_AUDIT: list[dict[str, str]] = []


def reset_for_tests() -> None:
    with _LOCK:
        _ENVELOPES.clear()
        _CONFIRMATIONS.clear()
        _SUBMISSIONS.clear()
        _AUDIT.clear()


def put_envelope(item: ExecutionEnvelope) -> ExecutionEnvelope:
    with _LOCK:
        current = _ENVELOPES.get(item.envelope_hash)
        if current != item:
            _ENVELOPES[item.envelope_hash] = item
        _AUDIT.append({"event": "envelope", "hash": item.envelope_hash, "state": item.state.value})
        return _ENVELOPES[item.envelope_hash]


def envelope(envelope_hash: str) -> ExecutionEnvelope | None:
    with _LOCK:
        return _ENVELOPES.get(envelope_hash)


def put_confirmation(item: HumanConfirmation) -> HumanConfirmation:
    with _LOCK:
        _CONFIRMATIONS[item.envelope_hash] = item
        _AUDIT.append({"event": "confirmed", "hash": item.envelope_hash, "actor": item.actor_id})
        return item


def confirmation(envelope_hash: str) -> HumanConfirmation | None:
    with _LOCK:
        return _CONFIRMATIONS.get(envelope_hash)


def put_submission(item: GatewaySubmission) -> GatewaySubmission:
    with _LOCK:
        previous = _SUBMISSIONS.get(item.envelope_hash)
        if previous is not None and previous.attempt_count > item.attempt_count:
            return previous
        _SUBMISSIONS[item.envelope_hash] = item
        _AUDIT.append(
            {"event": "submission", "hash": item.envelope_hash, "state": item.state.value}
        )
        return item


def submission(envelope_hash: str) -> GatewaySubmission | None:
    with _LOCK:
        return _SUBMISSIONS.get(envelope_hash)


def list_submissions() -> list[GatewaySubmission]:
    with _LOCK:
        return list(_SUBMISSIONS.values())


def audit() -> list[dict[str, str]]:
    with _LOCK:
        return list(_AUDIT)
