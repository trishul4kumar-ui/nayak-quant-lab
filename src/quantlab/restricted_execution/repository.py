"""In-process audit store for gateway state; no broker credentials or payload mutation."""
# ruff: noqa: E501

from __future__ import annotations

from pathlib import Path
from threading import Lock
from typing import cast

from quantlab.control_plane.sqlite import ControlPlaneSqlite
from quantlab.realtime_data.hashing import sha256
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
_DURABLE: ControlPlaneSqlite | None = None


def configure_durable_store(path: Path) -> None:
    """Enable the local SQLite implementation for the restricted gateway process."""
    global _DURABLE
    if _DURABLE is not None:
        _DURABLE.close()
    _DURABLE = ControlPlaneSqlite(path)


def disable_durable_store() -> None:
    """Return to the explicit in-memory test implementation."""
    global _DURABLE
    if _DURABLE is not None:
        _DURABLE.close()
    _DURABLE = None


def reset_for_tests() -> None:
    # Test isolation only. Runtime control-plane state is never reset implicitly.
    from quantlab.safety.kill_switch import reset_for_tests as reset_kill_switches

    reset_kill_switches()
    disable_durable_store()
    with _LOCK:
        _ENVELOPES.clear()
        _CONFIRMATIONS.clear()
        _SUBMISSIONS.clear()
        _AUDIT.clear()


def put_envelope(item: ExecutionEnvelope) -> ExecutionEnvelope:
    _persist("execution_envelope", item.envelope_hash, item, immutable=False, event="envelope")
    with _LOCK:
        current = _ENVELOPES.get(item.envelope_hash)
        if current != item:
            _ENVELOPES[item.envelope_hash] = item
        _AUDIT.append({"event": "envelope", "hash": item.envelope_hash, "state": item.state.value})
        return _ENVELOPES[item.envelope_hash]


def envelope(envelope_hash: str) -> ExecutionEnvelope | None:
    stored = _load("execution_envelope", envelope_hash, ExecutionEnvelope)
    if stored is not None:
        return cast(ExecutionEnvelope, stored)
    with _LOCK:
        return _ENVELOPES.get(envelope_hash)


def put_confirmation(item: HumanConfirmation) -> HumanConfirmation:
    _persist("human_confirmation", item.envelope_hash, item, immutable=True, event="confirmed")
    with _LOCK:
        _CONFIRMATIONS[item.envelope_hash] = item
        _AUDIT.append({"event": "confirmed", "hash": item.envelope_hash, "actor": item.actor_id})
        return item


def confirmation(envelope_hash: str) -> HumanConfirmation | None:
    stored = _load("human_confirmation", envelope_hash, HumanConfirmation)
    if stored is not None:
        return cast(HumanConfirmation, stored)
    with _LOCK:
        return _CONFIRMATIONS.get(envelope_hash)


def put_submission(item: GatewaySubmission) -> GatewaySubmission:
    _persist("gateway_submission", item.envelope_hash, item, immutable=False, event="submission")
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
    stored = _load("gateway_submission", envelope_hash, GatewaySubmission)
    if stored is not None:
        return cast(GatewaySubmission, stored)
    with _LOCK:
        return _SUBMISSIONS.get(envelope_hash)


def list_submissions() -> list[GatewaySubmission]:
    if _DURABLE is not None:
        return [
            GatewaySubmission.model_validate(row)
            for row in _DURABLE.list_latest("gateway_submission")
        ]
    with _LOCK:
        return list(_SUBMISSIONS.values())


def audit() -> list[dict[str, str]]:
    if _DURABLE is not None:
        return [{key: str(value) for key, value in row.items()} for row in _DURABLE.audit()]
    with _LOCK:
        return list(_AUDIT)


def _persist(
    namespace: str,
    identity: str,
    item: ExecutionEnvelope | HumanConfirmation | GatewaySubmission,
    *,
    immutable: bool,
    event: str,
) -> None:
    if _DURABLE is None:
        return
    payload = item.model_dump(mode="json")
    _DURABLE.append(
        namespace=namespace,
        identity=identity,
        payload=payload,
        payload_hash=sha256(payload),
        immutable=immutable,
        event=event,
    )


def _load(
    namespace: str,
    identity: str,
    model: type[ExecutionEnvelope] | type[HumanConfirmation] | type[GatewaySubmission],
) -> ExecutionEnvelope | HumanConfirmation | GatewaySubmission | None:
    if _DURABLE is None:
        return None
    payload = _DURABLE.get(namespace, identity)
    return model.model_validate(payload) if payload is not None else None
