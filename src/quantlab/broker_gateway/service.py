"""Read-only broker gateway. Connects. Does not trade."""

from __future__ import annotations

from datetime import UTC, datetime

from quantlab.broker_gateway.audit import history
from quantlab.broker_gateway.audit import record as record_audit
from quantlab.broker_gateway.audit import reset_for_tests as reset_audit
from quantlab.broker_gateway.errors import BrokerGatewayError, BrokerWriteError
from quantlab.broker_gateway.kite import KiteReadOnlyAdapter
from quantlab.broker_gateway.mock import MockBrokerAdapter
from quantlab.broker_gateway.models import (
    BrokerHealth,
    BrokerProfileSnapshot,
    GatewayIncident,
    GatewaySnapshotBundle,
    InternalBooks,
    MockScenario,
    ReconResult,
    ReconStatus,
)
from quantlab.broker_gateway.protocol import BrokerAdapter
from quantlab.broker_gateway.reconcile import reconcile as run_reconcile
from quantlab.broker_gateway.repository import (
    get_bundle,
    last_bundle,
    last_recon,
    list_bundles,
    list_incidents,
    list_recons,
    put_bundle,
    put_incident,
    put_recon,
)
from quantlab.broker_gateway.repository import reset_for_tests as reset_repo
from quantlab.broker_gateway.secrets import redact
from quantlab.broker_gateway.state import ConnectionState, current, force, is_healthy, transition
from quantlab.broker_gateway.state import reset_for_tests as reset_state
from quantlab.core.config import LiveSafetyGates
from quantlab.release.service import last_result as last_cert
from quantlab.release.state import current as cert_state
from quantlab.safety.kill_switch import live_release_blocked

_ADAPTER: BrokerAdapter | None = None


def reset_for_tests() -> None:
    global _ADAPTER
    reset_state()
    reset_repo()
    reset_audit()
    _ADAPTER = None


def _adapter() -> BrokerAdapter:
    global _ADAPTER
    if _ADAPTER is None:
        _ADAPTER = MockBrokerAdapter()
    return _ADAPTER


def set_adapter(adapter: BrokerAdapter) -> None:
    global _ADAPTER
    _ADAPTER = adapter


def select_adapter(name: str) -> None:
    """Select an explicit observation adapter. No selection can enable writes."""
    if name == "mock":
        set_adapter(MockBrokerAdapter())
        return
    if name == "kite":
        set_adapter(KiteReadOnlyAdapter.from_environment())
        return
    raise BrokerGatewayError(f"unknown read-only broker adapter: {name}")


def _assert_safety() -> LiveSafetyGates:
    gates = LiveSafetyGates()
    if gates.live_trading or gates.broker_write_enabled or not live_release_blocked():
        raise BrokerGatewayError("read-only broker gateway refuses a live or write-enabled state")
    return gates


def connect(
    scenario: MockScenario | str | None = None, *, adapter_name: str | None = None
) -> BrokerHealth:
    _assert_safety()
    before_cert = cert_state()
    if adapter_name is not None:
        select_adapter(adapter_name)
    elif scenario is not None:
        value = MockScenario(scenario) if isinstance(scenario, str) else scenario
        set_adapter(MockBrokerAdapter(value))
    adapter = _adapter()
    if current() is ConnectionState.DISCONNECTED:
        transition(ConnectionState.CONNECTING)
    try:
        health = adapter.connect()
    except Exception:
        if current() is ConnectionState.CONNECTING:
            transition(ConnectionState.BLOCKED)
        put_incident(
            GatewayIncident(
                incident_id="inc-connect",
                kind="connection_failure",
                detail="connect failed",
            )
        )
        raise
    if health.stale:
        if current() is ConnectionState.CONNECTING:
            transition(ConnectionState.CONNECTED_READ_ONLY)
        if current() is ConnectionState.CONNECTED_READ_ONLY:
            transition(ConnectionState.STALE)
    elif current() is ConnectionState.CONNECTING:
        transition(ConnectionState.CONNECTED_READ_ONLY)
    record_audit(
        {
            "event": "connect",
            "state": current().value,
            "adapter_id": adapter.adapter_id,
            "credential": redact(),
            "live_trading": False,
        }
    )
    if cert_state() != before_cert or LiveSafetyGates().live_trading:
        raise BrokerGatewayError(
            "read-only connect attempted to alter release or live-trading state"
        )
    return health.model_copy(
        update={
            "state": current().value,
            "healthy": is_healthy(),
            "live_trading": False,
            "write_enabled": False,
            "broker_connected": current()
            in {
                ConnectionState.CONNECTED_READ_ONLY,
                ConnectionState.STALE,
                ConnectionState.DEGRADED,
            },
        }
    )


def disconnect() -> BrokerHealth:
    adapter = _adapter()
    adapter.disconnect()
    if current() is not ConnectionState.DISCONNECTED:
        if current() is ConnectionState.BLOCKED or current() in {
            ConnectionState.CONNECTED_READ_ONLY,
            ConnectionState.DEGRADED,
            ConnectionState.STALE,
            ConnectionState.RECONCILIATION_REQUIRED,
        }:
            transition(ConnectionState.DISCONNECTED)
        else:
            force(ConnectionState.DISCONNECTED)
    record_audit({"event": "disconnect", "state": current().value, "live_trading": False})
    return health()


def health() -> BrokerHealth:
    gates = _assert_safety()
    state = current()
    return BrokerHealth(
        state=state.value,
        healthy=is_healthy(state),
        stale=state is ConnectionState.STALE,
        live_trading=gates.live_trading,
        write_enabled=gates.broker_write_enabled,
        broker_connected=state is ConnectionState.CONNECTED_READ_ONLY,
        credential_redacted=redact(),
    )


def profile() -> BrokerProfileSnapshot:
    _assert_safety()
    item = _adapter().profile()
    record_audit(
        {
            "event": "profile",
            "adapter_id": _adapter().adapter_id,
            "account_id_hash": item.account_id_hash,
            "live_trading": False,
        }
    )
    return item


def snapshot() -> GatewaySnapshotBundle:
    _assert_safety()
    bundle = _adapter().snapshot()
    stored = put_bundle(bundle)
    record_audit(
        {
            "event": "snapshot",
            "bundle_id": stored.bundle_id,
            "hash": stored.payload_hash,
            "live_trading": False,
        }
    )
    return stored


def reconcile(books: InternalBooks | None = None) -> ReconResult:
    bundle = last_bundle() or snapshot()
    result = run_reconcile(bundle, books)
    put_recon(result)
    if result.status in {ReconStatus.MISMATCH, ReconStatus.BLOCKED, ReconStatus.PARTIAL}:
        if current() is ConnectionState.CONNECTED_READ_ONLY:
            transition(ConnectionState.RECONCILIATION_REQUIRED)
        put_incident(
            GatewayIncident(
                incident_id=result.reconciliation_id,
                kind=result.status.value,
                detail="reconciliation differences retained",
            )
        )
    record_audit(
        {
            "event": "reconcile",
            "status": result.status.value,
            "hash": result.payload_hash,
            "live_trading": False,
        }
    )
    return result


def place_order(*_args: object, **_kwargs: object) -> None:
    put_incident(
        GatewayIncident(
            incident_id="inc-write",
            kind="broker_write_attempt",
            detail="write path disabled",
            created_at=datetime(2024, 1, 2, tzinfo=UTC),
        )
    )
    raise BrokerWriteError("write path disabled; BROKER_WRITE_ENABLED=false")


def cancel_order(*_args: object, **_kwargs: object) -> None:
    raise BrokerWriteError("write path disabled; BROKER_WRITE_ENABLED=false")


def modify_order(*_args: object, **_kwargs: object) -> None:
    raise BrokerWriteError("write path disabled; BROKER_WRITE_ENABLED=false")


def inspect(item_id: str = "last") -> GatewaySnapshotBundle | None:
    return get_bundle(item_id)


def list_connections() -> list[GatewaySnapshotBundle]:
    return list_bundles()


def last_snapshot() -> GatewaySnapshotBundle | None:
    return last_bundle()


def last_reconciliation() -> ReconResult | None:
    return last_recon()


def incidents() -> list[GatewayIncident]:
    return list_incidents()


def recon_history() -> list[ReconResult]:
    return list_recons()


def audit_history() -> list[dict[str, object]]:
    return history()


def matching_internal_books() -> InternalBooks:
    """Internal books aligned to the mock normal scenario. Still not live."""
    return InternalBooks(
        cash=100_000.0,
        reserved_cash=0.0,
        positions=(("SEC-TCS", 10.0, 3500.0),),
        orders=("BRK-ORD-1",),
        fills=("BRK-FILL-1",),
    )


def certification_untouched() -> str:
    result = last_cert()
    return result.state.value if result is not None else cert_state().value
