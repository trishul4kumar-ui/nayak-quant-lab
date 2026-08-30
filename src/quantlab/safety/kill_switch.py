"""Kill switches. Activation is fail-safe. A kill never creates an order."""

from __future__ import annotations

from datetime import UTC, datetime
from threading import Lock

from quantlab.data.fabric.checksums import sha256_bytes
from quantlab.safety.models import KillScope, KillSwitch

_LOCK = Lock()
_SWITCHES: dict[KillScope, KillSwitch] = {}


def _hash(scope: KillScope, reason: str, active: bool) -> str:
    payload = f"{scope.value}|{reason}|{active}".encode()
    return sha256_bytes(payload)


def _default(scope: KillScope, *, active: bool, reason: str) -> KillSwitch:
    now = datetime(2024, 1, 2, tzinfo=UTC)
    return KillSwitch(
        switch_id=f"kill-{scope.value}",
        scope=scope,
        reason=reason,
        created_at=now,
        created_by="system",
        activation_source="fail_safe_default",
        active=active,
        timestamp=now,
        audit_hash=_hash(scope, reason, active),
    )


def reset_for_tests() -> None:
    with _LOCK:
        _SWITCHES.clear()
        for scope in KillScope:
            live = scope is KillScope.LIVE_RELEASE
            _SWITCHES[scope] = _default(
                scope,
                active=live,
                reason="LIVE_RELEASE_KILL on while LIVE_TRADING=false"
                if live
                else "inactive",
            )


reset_for_tests()


def snapshot() -> dict[KillScope, KillSwitch]:
    with _LOCK:
        return dict(_SWITCHES)


def is_active(scope: KillScope) -> bool:
    return snapshot()[scope].active


def live_release_blocked() -> bool:
    switches = snapshot()
    return switches[KillScope.LIVE_RELEASE].active or switches[KillScope.GLOBAL].active


def activate(scope: KillScope, *, reason: str, created_by: str = "human") -> KillSwitch:
    now = datetime(2024, 1, 2, tzinfo=UTC)
    item = KillSwitch(
        switch_id=f"kill-{scope.value}",
        scope=scope,
        reason=reason,
        created_at=now,
        created_by=created_by,
        activation_source="explicit",
        active=True,
        timestamp=now,
        audit_hash=_hash(scope, reason, True),
    )
    with _LOCK:
        _SWITCHES[scope] = item
    return item


def deactivate(scope: KillScope, *, reason: str, created_by: str = "human") -> KillSwitch:
    if scope is KillScope.LIVE_RELEASE:
        item = activate(
            KillScope.LIVE_RELEASE,
            reason="LIVE_RELEASE_KILL cannot be cleared while LIVE_TRADING=false",
            created_by=created_by,
        )
        return item
    now = datetime(2024, 1, 2, tzinfo=UTC)
    item = KillSwitch(
        switch_id=f"kill-{scope.value}",
        scope=scope,
        reason=reason,
        created_at=now,
        created_by=created_by,
        activation_source="explicit_unkill",
        active=False,
        timestamp=now,
        audit_hash=_hash(scope, reason, False),
    )
    with _LOCK:
        _SWITCHES[scope] = item
    return item
