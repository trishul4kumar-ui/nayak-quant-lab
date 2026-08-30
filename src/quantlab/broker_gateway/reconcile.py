"""Three-way reconciliation. Never silently repair."""

from __future__ import annotations

from datetime import UTC, datetime

from quantlab.broker_gateway.mapping import mapping_is_ambiguous
from quantlab.broker_gateway.models import (
    GatewaySnapshotBundle,
    InternalBooks,
    ReconBreak,
    ReconResult,
    ReconStatus,
)
from quantlab.data.fabric.checksums import sha256_bytes


def reconcile(
    bundle: GatewaySnapshotBundle,
    books: InternalBooks | None = None,
    *,
    as_of: datetime | None = None,
) -> ReconResult:
    books = books or InternalBooks()
    now = as_of or datetime(2024, 1, 2, tzinfo=UTC)
    breaks: list[ReconBreak] = []
    unknown_orders: list[str] = []
    orphan_fills: list[str] = []
    missing_fills: list[str] = []

    broker_cash = bundle.account.available_cash
    if abs(broker_cash - books.cash) > 1e-9:
        breaks.append(
            ReconBreak(
                kind="cash_reconciliation_break",
                broker_cash=broker_cash,
                internal_cash=books.cash,
                detail="cash identity mismatch; not repaired",
            )
        )

    internal_qty = {item[0]: item[1] for item in books.positions}
    for position in bundle.positions:
        key = position.security_id
        qty = internal_qty.get(key)
        if qty is None:
            breaks.append(
                ReconBreak(
                    kind="position_reconciliation_break",
                    instrument=key,
                    broker_qty=position.quantity,
                    internal_qty=0.0,
                    delta_qty=position.quantity,
                    detail="broker position missing internally; not invented",
                )
            )
        elif abs(qty - position.quantity) > 1e-9:
            breaks.append(
                ReconBreak(
                    kind="position_reconciliation_break",
                    instrument=key,
                    broker_qty=position.quantity,
                    internal_qty=qty,
                    delta_qty=position.quantity - qty,
                    detail="position quantity mismatch; not repaired",
                )
            )

    known_orders = set(books.orders)
    for order in bundle.orders:
        if order.broker_order_id not in known_orders:
            unknown_orders.append(order.broker_order_id)
            breaks.append(
                ReconBreak(
                    kind="unknown_broker_order",
                    instrument=order.broker_instrument_id,
                    detail=f"unknown broker order {order.broker_order_id}",
                )
            )

    known_fills = set(books.fills)
    order_ids = {item.broker_order_id for item in bundle.orders}
    seen_fills: set[str] = set()
    for fill in bundle.fills:
        if fill.broker_fill_id in seen_fills:
            breaks.append(
                ReconBreak(
                    kind="duplicate_external_event",
                    detail=f"duplicate fill {fill.broker_fill_id}",
                )
            )
        seen_fills.add(fill.broker_fill_id)
        if fill.broker_order_id not in order_ids:
            orphan_fills.append(fill.broker_fill_id)
            breaks.append(
                ReconBreak(
                    kind="orphan_broker_fill",
                    detail=f"orphan fill {fill.broker_fill_id}",
                )
            )
        if fill.broker_fill_id not in known_fills:
            missing_fills.append(fill.broker_fill_id)

    if mapping_is_ambiguous(bundle.mappings):
        breaks.append(
            ReconBreak(
                kind="instrument_mapping_ambiguity",
                detail="ambiguous instrument mapping; fail closed",
            )
        )

    if bundle.provenance.source_sequence == 0:
        breaks.append(
            ReconBreak(
                kind="event_ordering_failure",
                detail="broker sequence unavailable or out of order",
            )
        )

    if unknown_orders or orphan_fills:
        status = ReconStatus.BLOCKED
    elif breaks:
        status = ReconStatus.MISMATCH
    elif missing_fills and not books.fills:
        status = ReconStatus.PARTIAL
    else:
        status = ReconStatus.RECONCILED

    material = f"{status.value}|" + "|".join(item.kind for item in breaks)
    return ReconResult(
        reconciliation_id=f"recon-{sha256_bytes(material.encode())[:12]}",
        status=status,
        captured_at=now,
        breaks=tuple(breaks),
        unknown_broker_orders=tuple(unknown_orders),
        orphan_fills=tuple(orphan_fills),
        missing_fills=tuple(dict.fromkeys(missing_fills)),
        payload_hash=sha256_bytes(material.encode()),
    )
