from __future__ import annotations

from datetime import timedelta

import pytest

from quantlab.broker_gateway.mock import MockBrokerAdapter
from quantlab.broker_gateway.service import matching_internal_books
from quantlab.reconciliation.models import ReconciliationStatus, ReconciliationTolerances
from quantlab.reconciliation.repository import reset_for_tests
from quantlab.reconciliation.service import internal_from_books, reconcile


@pytest.fixture(autouse=True)
def clear_reports() -> None:
    reset_for_tests()


@pytest.mark.parametrize("dimension", ["orders", "positions", "holdings"])
@pytest.mark.parametrize("side", ["broker", "internal"])
def test_duplicate_keys_are_never_collapsed(dimension: str, side: str) -> None:
    broker = MockBrokerAdapter().snapshot()
    internal = internal_from_books(
        matching_internal_books(), observed_at=broker.provenance.source_timestamp
    )
    if side == "broker":
        rows = getattr(broker, dimension)
        broker = broker.model_copy(update={dimension: (*rows, rows[0])})
    else:
        rows = getattr(internal, dimension)
        internal = internal.model_copy(update={dimension: (*rows, rows[0])})
    report = reconcile(broker, internal)
    assert report.status is ReconciliationStatus.RECONCILIATION_BREAK
    assert any(row.detail == f"duplicate {side} identifier" for row in report.exceptions)


@pytest.mark.parametrize(
    ("dimension", "field"),
    [("orders", "broker_order_id"), ("positions", "security_id"), ("holdings", "security_id")],
)
def test_empty_identity_never_matches(dimension: str, field: str) -> None:
    broker = MockBrokerAdapter().snapshot()
    internal = internal_from_books(
        matching_internal_books(), observed_at=broker.provenance.source_timestamp
    )
    left = getattr(broker, dimension)[0].model_copy(update={field: ""})
    right = getattr(internal, dimension)[0].model_copy(update={field: ""})
    broker = broker.model_copy(update={dimension: (left,)})
    internal = internal.model_copy(update={dimension: (right,)})
    report = reconcile(broker, internal)
    assert report.status is ReconciliationStatus.RECONCILIATION_BREAK
    assert any(row.detail == "empty broker identifier" for row in report.exceptions)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("quantity", float("nan"), "order quantity is not finite"),
        ("quantity", float("inf"), "order quantity is not finite"),
        ("quantity", 0.0, "order quantity is not positive"),
        ("price", float("nan"), "order price is not finite"),
        ("price", float("inf"), "order price is not finite"),
        ("price", None, "order price unavailable"),
        ("price", 0.0, "order price is not positive"),
        ("status", "", "order status unavailable"),
        ("observed_at", None, "order timestamp unavailable"),
    ],
)
def test_invalid_or_incomplete_order_is_not_a_match(
    field: str, value: object, message: str
) -> None:
    broker = MockBrokerAdapter().snapshot()
    internal = internal_from_books(
        matching_internal_books(), observed_at=broker.provenance.source_timestamp
    )
    changed = internal.orders[0].model_copy(update={field: value})
    report = reconcile(broker, internal.model_copy(update={"orders": (changed,)}))
    assert report.status not in {
        ReconciliationStatus.MATCH, ReconciliationStatus.MATCH_WITH_TOLERANCE
    }
    assert any(row.detail == message for row in report.exceptions)
    assert "order:BRK-ORD-1" not in report.matched_dimensions


def test_both_sides_missing_order_price_are_not_an_exact_match() -> None:
    broker = MockBrokerAdapter().snapshot()
    internal = internal_from_books(
        matching_internal_books(), observed_at=broker.provenance.source_timestamp
    )
    broker = broker.model_copy(
        update={"orders": (broker.orders[0].model_copy(update={"price": None}),)}
    )
    internal = internal.model_copy(
        update={"orders": (internal.orders[0].model_copy(update={"price": None}),)}
    )
    report = reconcile(broker, internal)
    assert report.status is ReconciliationStatus.MISMATCH
    assert any(row.detail == "order price unavailable" for row in report.exceptions)


@pytest.mark.parametrize("field", ["quantity", "average_price", "market_value", "realized_pnl"])
def test_nonfinite_internal_position_values_cannot_match(field: str) -> None:
    broker = MockBrokerAdapter().snapshot()
    internal = internal_from_books(
        matching_internal_books(), observed_at=broker.provenance.source_timestamp
    )
    changed = internal.positions[0].model_copy(update={field: float("inf")})
    report = reconcile(broker, internal.model_copy(update={"positions": (changed,)}))
    assert report.status is ReconciliationStatus.RECONCILIATION_BREAK
    assert any(row.detail == "comparison value is not finite" for row in report.exceptions)


def test_tolerated_order_difference_is_not_an_exact_match() -> None:
    broker = MockBrokerAdapter().snapshot()
    internal = internal_from_books(
        matching_internal_books(), observed_at=broker.provenance.source_timestamp
    )
    changed = internal.orders[0].model_copy(
        update={"price": 3500.005, "observed_at": internal.observed_at + timedelta(seconds=1)}
    )
    report = reconcile(
        broker,
        internal.model_copy(update={"orders": (changed,)}),
        tolerances=ReconciliationTolerances(price_absolute=0.01, timestamp_seconds=5),
    )
    assert report.status is ReconciliationStatus.MATCH_WITH_TOLERANCE
    assert "order:BRK-ORD-1" in report.tolerance_dimensions
    assert "order:BRK-ORD-1" not in report.matched_dimensions
