"""Deterministic comparison service. It only reports differences; it never repairs them."""

from __future__ import annotations

from datetime import UTC, datetime

from quantlab.broker_gateway.models import GatewaySnapshotBundle, InternalBooks
from quantlab.broker_gateway.secrets import account_id_hash
from quantlab.realtime_data.hashing import sha256
from quantlab.reconciliation.models import (
    ExceptionStatus,
    InternalAccountSnapshot,
    InternalFill,
    InternalOrder,
    InternalPosition,
    OrderMatchStatus,
    ReconciliationException,
    ReconciliationReport,
    ReconciliationStatus,
    ReconciliationTolerances,
)
from quantlab.reconciliation.repository import put, update_exception

_ALLOWED_TRANSITIONS: frozenset[tuple[ExceptionStatus, ExceptionStatus]] = frozenset(
    {
        (ExceptionStatus.OPEN, ExceptionStatus.ACKNOWLEDGED),
        (ExceptionStatus.ACKNOWLEDGED, ExceptionStatus.INVESTIGATING),
        (ExceptionStatus.INVESTIGATING, ExceptionStatus.EXPLAINED),
        (ExceptionStatus.INVESTIGATING, ExceptionStatus.RESOLVED),
        (ExceptionStatus.INVESTIGATING, ExceptionStatus.ESCALATED),
    }
)


def internal_from_books(books: InternalBooks, *, observed_at: datetime) -> InternalAccountSnapshot:
    """Compatibility bridge for the existing mock-only internal books fixture."""
    positions = tuple(
        InternalPosition(
            security_id=item[0],
            quantity=item[1],
            average_price=item[2],
            market_value=3510.0 * item[1],
            realized_pnl=0.0,
        )
        for item in books.positions
    )
    orders = tuple(
        InternalOrder(
            broker_order_id=item,
            status="complete",
            quantity=10.0,
            price=3500.0,
            observed_at=observed_at,
        )
        for item in books.orders
    )
    fills = tuple(
        InternalFill(broker_fill_id=item, broker_order_id="BRK-ORD-1", quantity=10.0, price=3500.0)
        for item in books.fills
    )
    return InternalAccountSnapshot(
        snapshot_id=f"internal-{sha256({'cash': books.cash, 'positions': books.positions})[:12]}",
        account_id_hash=account_id_hash("mock-account"),
        observed_at=observed_at,
        available_cash=books.cash,
        utilized_margin=5_000.0,
        available_margin=20_000.0,
        holdings=(
            InternalPosition(
                security_id="SEC-TCS",
                quantity=10.0,
                average_price=3400.0,
            ),
        ),
        positions=positions,
        orders=orders,
        fills=fills,
    )


def reconcile(
    broker: GatewaySnapshotBundle | None,
    internal: InternalAccountSnapshot | None,
    *,
    tolerances: ReconciliationTolerances | None = None,
    observed_at: datetime | None = None,
) -> ReconciliationReport:
    """Compare snapshots without mutating either source or invoking any broker operation."""
    policy = tolerances or ReconciliationTolerances()
    now = observed_at or _observed_at(broker, internal)
    if broker is None:
        return _report(
            None, internal, policy, ReconciliationStatus.BROKER_UNAVAILABLE, (), (), (), now
        )
    if internal is None:
        return _report(
            broker, None, policy, ReconciliationStatus.INTERNAL_STATE_UNAVAILABLE, (), (), (), now
        )
    if _is_stale(broker, internal, policy):
        exc = _exception(
            "snapshot",
            "freshness",
            "critical",
            "broker/internal snapshot timestamps exceed tolerance",
            now,
        )
        return _report(broker, internal, policy, ReconciliationStatus.STALE, (exc,), (), (), now)

    exceptions: list[ReconciliationException] = []
    matches: list[str] = []
    tolerated: list[str] = []
    _compare_identity(broker, internal, exceptions, matches, now)
    _compare_scalar(
        "cash",
        broker.account.available_cash,
        internal.available_cash,
        policy.cash_absolute,
        exceptions,
        matches,
        tolerated,
        now,
    )
    _compare_scalar(
        "utilized_margin",
        broker.margins.utilized_margin,
        internal.utilized_margin,
        policy.cash_absolute,
        exceptions,
        matches,
        tolerated,
        now,
    )
    _compare_scalar(
        "available_margin",
        broker.margins.available_margin,
        internal.available_margin,
        policy.cash_absolute,
        exceptions,
        matches,
        tolerated,
        now,
    )
    _compare_positions(broker, internal, policy, exceptions, matches, tolerated, now)
    _compare_holdings(broker, internal, policy, exceptions, matches, tolerated, now)
    _compare_orders(broker, internal, policy, exceptions, matches, now)
    _compare_fills(broker, internal, exceptions, matches, now)

    critical = any(item.severity == "critical" for item in exceptions)
    status = (
        ReconciliationStatus.RECONCILIATION_BREAK
        if critical
        else ReconciliationStatus.MISMATCH
        if exceptions
        else ReconciliationStatus.MATCH_WITH_TOLERANCE
        if tolerated
        else ReconciliationStatus.MATCH
    )
    return _report(
        broker, internal, policy, status, tuple(exceptions), tuple(matches), tuple(tolerated), now
    )


def transition_exception(
    item: ReconciliationException, target: ExceptionStatus
) -> ReconciliationException:
    if (item.status, target) not in _ALLOWED_TRANSITIONS:
        raise ValueError(f"illegal reconciliation exception transition: {item.status} -> {target}")
    return update_exception(item.model_copy(update={"status": target}))


def _compare_identity(
    broker: GatewaySnapshotBundle,
    internal: InternalAccountSnapshot,
    exceptions: list[ReconciliationException],
    matches: list[str],
    now: datetime,
) -> None:
    invalid_mappings = [
        item
        for item in broker.mappings
        if item.ambiguous or item.security_id.startswith("UNMAPPED:")
    ]
    if invalid_mappings:
        exceptions.append(
            _exception(
                "identity",
                "security_master",
                "critical",
                "broker instrument mapping unresolved",
                now,
            )
        )
    elif broker.profile.account_id_hash != internal.account_id_hash:
        exceptions.append(
            _exception("identity", "account", "critical", "account identity hash mismatch", now)
        )
    else:
        matches.append("identity")


def _compare_scalar(
    name: str,
    broker_value: float | None,
    internal_value: float | None,
    tolerance: float,
    exceptions: list[ReconciliationException],
    matches: list[str],
    tolerated: list[str],
    now: datetime,
) -> None:
    if broker_value is None or internal_value is None:
        exceptions.append(_exception(name, name, "warning", "comparison unavailable", now))
    elif broker_value == internal_value:
        matches.append(name)
    elif abs(broker_value - internal_value) <= tolerance:
        tolerated.append(name)
    else:
        exceptions.append(
            _exception(
                name,
                name,
                "warning",
                "value outside explicit tolerance",
                now,
                broker_value,
                internal_value,
            )
        )


def _compare_positions(
    broker: GatewaySnapshotBundle,
    internal: InternalAccountSnapshot,
    policy: ReconciliationTolerances,
    exceptions: list[ReconciliationException],
    matches: list[str],
    tolerated: list[str],
    now: datetime,
) -> None:
    broker_rows = {item.security_id: item for item in broker.positions}
    internal_rows = {item.security_id: item for item in internal.positions}
    for security_id in sorted(set(broker_rows) | set(internal_rows)):
        left, right = broker_rows.get(security_id), internal_rows.get(security_id)
        if left is None or right is None:
            exceptions.append(
                _exception(
                    "position", security_id, "critical", "broker/internal position missing", now
                )
            )
            continue
        _compare_scalar(
            f"position_quantity:{security_id}",
            left.quantity,
            right.quantity,
            policy.quantity_absolute,
            exceptions,
            matches,
            tolerated,
            now,
        )
        _compare_scalar(
            f"average_price:{security_id}",
            left.average_price,
            right.average_price,
            policy.price_absolute,
            exceptions,
            matches,
            tolerated,
            now,
        )
        broker_value = left.last_price * left.quantity if left.last_price is not None else None
        _compare_scalar(
            f"market_value:{security_id}",
            broker_value,
            right.market_value,
            policy.value_absolute,
            exceptions,
            matches,
            tolerated,
            now,
        )
        _compare_scalar(
            f"realized_pnl:{security_id}",
            left.realized_pnl,
            right.realized_pnl,
            policy.value_absolute,
            exceptions,
            matches,
            tolerated,
            now,
        )


def _compare_holdings(
    broker: GatewaySnapshotBundle,
    internal: InternalAccountSnapshot,
    policy: ReconciliationTolerances,
    exceptions: list[ReconciliationException],
    matches: list[str],
    tolerated: list[str],
    now: datetime,
) -> None:
    broker_rows = {item.security_id: item for item in broker.holdings}
    internal_rows = {item.security_id: item for item in internal.holdings}
    for security_id in sorted(set(broker_rows) | set(internal_rows)):
        left, right = broker_rows.get(security_id), internal_rows.get(security_id)
        if left is None or right is None:
            exceptions.append(
                _exception(
                    "holding", security_id, "critical", "broker/internal holding missing", now
                )
            )
            continue
        _compare_scalar(
            f"holding_quantity:{security_id}",
            left.quantity,
            right.quantity,
            policy.quantity_absolute,
            exceptions,
            matches,
            tolerated,
            now,
        )
        _compare_scalar(
            f"holding_average_price:{security_id}",
            left.average_cost,
            right.average_price,
            policy.price_absolute,
            exceptions,
            matches,
            tolerated,
            now,
        )


def _compare_orders(
    broker: GatewaySnapshotBundle,
    internal: InternalAccountSnapshot,
    policy: ReconciliationTolerances,
    exceptions: list[ReconciliationException],
    matches: list[str],
    now: datetime,
) -> None:
    broker_rows = {item.broker_order_id: item for item in broker.orders}
    internal_rows = {item.broker_order_id: item for item in internal.orders}
    for order_id in sorted(set(broker_rows) | set(internal_rows)):
        left, right = broker_rows.get(order_id), internal_rows.get(order_id)
        if left is None:
            exceptions.append(
                _exception(
                    "order",
                    order_id,
                    "critical",
                    "internal order absent at broker",
                    now,
                    order_status=OrderMatchStatus.INTERNAL_ONLY,
                )
            )
        elif right is None:
            exceptions.append(
                _exception(
                    "order",
                    order_id,
                    "critical",
                    "broker order absent internally",
                    now,
                    order_status=OrderMatchStatus.BROKER_ONLY,
                )
            )
        elif left.status.lower() != right.status.lower():
            exceptions.append(
                _exception(
                    "order",
                    order_id,
                    "warning",
                    "order status mismatch",
                    now,
                    order_status=OrderMatchStatus.STATUS_MISMATCH,
                )
            )
        elif abs(left.quantity - right.quantity) > policy.quantity_absolute:
            exceptions.append(
                _exception(
                    "order",
                    order_id,
                    "warning",
                    "order quantity mismatch",
                    now,
                    order_status=OrderMatchStatus.QUANTITY_MISMATCH,
                )
            )
        elif (
            left.price is not None
            and right.price is not None
            and abs(left.price - right.price) > policy.price_absolute
        ):
            exceptions.append(
                _exception(
                    "order",
                    order_id,
                    "warning",
                    "order price mismatch",
                    now,
                    order_status=OrderMatchStatus.PRICE_MISMATCH,
                )
            )
        elif (
            right.observed_at is not None
            and abs((left.source_timestamp - right.observed_at).total_seconds())
            > policy.timestamp_seconds
        ):
            exceptions.append(
                _exception(
                    "order",
                    order_id,
                    "warning",
                    "order timestamp mismatch",
                    now,
                    order_status=OrderMatchStatus.TIMESTAMP_MISMATCH,
                )
            )
        else:
            matches.append(f"order:{order_id}")


def _compare_fills(
    broker: GatewaySnapshotBundle,
    internal: InternalAccountSnapshot,
    exceptions: list[ReconciliationException],
    matches: list[str],
    now: datetime,
) -> None:
    seen: set[str] = set()
    internal_ids = {item.broker_fill_id for item in internal.fills}
    broker_ids: set[str] = set()
    for fill in broker.fills:
        if fill.broker_fill_id in seen:
            exceptions.append(
                _exception(
                    "fill", fill.broker_fill_id, "critical", "duplicate broker fill identifier", now
                )
            )
            continue
        seen.add(fill.broker_fill_id)
        broker_ids.add(fill.broker_fill_id)
        if fill.broker_fill_id in internal_ids:
            matches.append(f"fill:{fill.broker_fill_id}")
        else:
            exceptions.append(
                _exception(
                    "fill", fill.broker_fill_id, "critical", "unknown broker fill identifier", now
                )
            )
    for missing in sorted(internal_ids - broker_ids):
        exceptions.append(
            _exception("fill", missing, "warning", "internal fill absent at broker", now)
        )


def _is_stale(
    broker: GatewaySnapshotBundle,
    internal: InternalAccountSnapshot,
    policy: ReconciliationTolerances,
) -> bool:
    return (
        abs((broker.provenance.source_timestamp - internal.observed_at).total_seconds())
        > policy.timestamp_seconds
    )


def _observed_at(
    broker: GatewaySnapshotBundle | None, internal: InternalAccountSnapshot | None
) -> datetime:
    if broker is not None:
        return broker.provenance.captured_at
    if internal is not None:
        return internal.observed_at
    return datetime.now(tz=UTC)


def _exception(
    dimension: str,
    key: str,
    severity: str,
    detail: str,
    now: datetime,
    broker_value: object | None = None,
    internal_value: object | None = None,
    order_status: OrderMatchStatus | None = None,
) -> ReconciliationException:
    digest = sha256({"dimension": dimension, "key": key, "detail": detail, "at": now.isoformat()})
    return ReconciliationException(
        exception_id=f"recon-exc-{digest[:12]}",
        dimension=dimension,
        key=key,
        severity=severity,
        detail=detail,
        broker_value=None if broker_value is None else str(broker_value),
        internal_value=None if internal_value is None else str(internal_value),
        order_status=order_status,
        created_at=now,
    )


def _report(
    broker: GatewaySnapshotBundle | None,
    internal: InternalAccountSnapshot | None,
    policy: ReconciliationTolerances,
    status: ReconciliationStatus,
    exceptions: tuple[ReconciliationException, ...],
    matches: tuple[str, ...],
    tolerated: tuple[str, ...],
    now: datetime,
) -> ReconciliationReport:
    material = {
        "broker": broker.bundle_id if broker else None,
        "internal": internal.snapshot_id if internal else None,
        "policy": policy.model_dump(mode="json"),
        "status": status.value,
        "exceptions": [item.model_dump(mode="json") for item in exceptions],
        "matches": matches,
        "tolerated": tolerated,
        "observed_at": now.isoformat(),
    }
    digest = sha256(material)
    report = ReconciliationReport(
        reconciliation_id=f"reconciliation-{digest[:12]}",
        broker_snapshot_id=broker.bundle_id if broker else None,
        internal_snapshot_id=internal.snapshot_id if internal else None,
        policy_version=policy.policy_version,
        tolerances=policy,
        status=status,
        exceptions=exceptions,
        reconciliation_hash=digest,
        observed_at=now,
        matched_dimensions=matches,
        tolerance_dimensions=tolerated,
    )
    return put(report)
