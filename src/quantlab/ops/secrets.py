"""Secret boundary. Values never appear in logs, CLI, UI, or ledger."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Protocol

from quantlab.ops.errors import OpsError, SecretExposureError
from quantlab.ops.models import SecretAccessAudit, SecretMetadata, SecretReference

FORBIDDEN_ENV = frozenset(
    {
        "BROKER_PASSWORD",
        "KITE_API_SECRET",
        "KITE_ACCESS_TOKEN",
        "ZERODHA_TOKEN",
        "LIVE_API_KEY",
        "LIVE_API_SECRET",
        "OPENALGO_API_KEY",
    }
)

_EXPIRED: set[str] = set()


class SecretProvider(Protocol):
    def reference(self, name: str) -> SecretReference: ...


def reset_for_tests() -> None:
    _EXPIRED.clear()


def reject_live_credentials() -> None:
    present = [name for name in FORBIDDEN_ENV if os.environ.get(name)]
    if present:
        raise OpsError(f"live credential env vars rejected: {', '.join(sorted(present))}")


def metadata(name: str, *, version: str = "1") -> SecretMetadata:
    return SecretMetadata(name=name, version=version, expired=name in _EXPIRED)


def mark_expired(name: str) -> None:
    _EXPIRED.add(name)


def reference(name: str) -> SecretReference:
    if name in FORBIDDEN_ENV:
        raise OpsError(f"ambiguous live credential {name} is rejected")
    if name in _EXPIRED:
        raise OpsError(f"secret {name} expired")
    return SecretReference(name=name, present=False, expires_at=None)


def redact(text: str, secrets: tuple[str, ...] = ()) -> str:
    redacted = text
    for item in secrets:
        if item:
            redacted = redacted.replace(item, "[REDACTED]")
    return redacted


def audit_access(*, name: str, actor: str, purpose: str) -> SecretAccessAudit:
    if purpose in {"log", "cli", "ui", "ledger", "exception"}:
        raise SecretExposureError("secret values must not appear in leakable channels")
    return SecretAccessAudit(
        name=name,
        actor=actor,
        timestamp=datetime(2024, 1, 2, tzinfo=UTC),
        purpose=purpose,
        leaked=False,
    )
