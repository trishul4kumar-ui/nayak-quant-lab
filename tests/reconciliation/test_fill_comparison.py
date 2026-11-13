from __future__ import annotations

import pytest
from pydantic import ValidationError

from quantlab.broker_gateway.mock import MockBrokerAdapter
from quantlab.broker_gateway.service import matching_internal_books
from quantlab.reconciliation.models import ReconciliationStatus, ReconciliationTolerances
from quantlab.reconciliation.repository import reset_for_tests
from quantlab.reconciliation.service import internal_from_books, reconcile


@pytest.fixture(autouse=True)
def clear_reports() -> None:
    reset_for_tests()


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("broker_order_id", "different-order", "fill order identity mismatch"),
        ("quantity", 2.0, "fill quantity mismatch"),
        ("price", 3600.0, "fill price mismatch"),
        ("price", float("nan"), "fill value is not finite"),
    ],
)
def test_same_identifier_does_not_hide_different_fill(
    field: str, value: object, message: str
) -> None:
    broker = MockBrokerAdapter().snapshot()
    internal = internal_from_books(
        matching_internal_books(), observed_at=broker.provenance.source_timestamp
    )
    changed = internal.fills[0].model_copy(update={field: value})
    report = reconcile(broker, internal.model_copy(update={"fills": (changed,)}))
    assert report.status is ReconciliationStatus.RECONCILIATION_BREAK
    assert any(row.detail == message for row in report.exceptions)
    assert "fill:BRK-FILL-1" not in report.matched_dimensions


@pytest.mark.parametrize("side", ["broker", "internal"])
def test_duplicate_fill_identity_is_critical(side: str) -> None:
    broker = MockBrokerAdapter().snapshot()
    internal = internal_from_books(
        matching_internal_books(), observed_at=broker.provenance.source_timestamp
    )
    if side == "broker":
        broker = broker.model_copy(update={"fills": (*broker.fills, broker.fills[0])})
    else:
        internal = internal.model_copy(update={"fills": (*internal.fills, internal.fills[0])})
    report = reconcile(broker, internal)
    assert report.status is ReconciliationStatus.RECONCILIATION_BREAK
    assert any(row.detail == f"duplicate {side} fill identifier" for row in report.exceptions)
    assert "fill:BRK-FILL-1" not in report.matched_dimensions


def test_fill_price_tolerance_is_explicitly_recorded() -> None:
    broker = MockBrokerAdapter().snapshot()
    internal = internal_from_books(
        matching_internal_books(), observed_at=broker.provenance.source_timestamp
    )
    changed = internal.fills[0].model_copy(update={"price": 3500.005})
    report = reconcile(
        broker,
        internal.model_copy(update={"fills": (changed,)}),
        tolerances=ReconciliationTolerances(price_absolute=0.01),
    )
    assert report.status is ReconciliationStatus.MATCH_WITH_TOLERANCE
    assert "fill:BRK-FILL-1" in report.tolerance_dimensions
    assert "fill:BRK-FILL-1" not in report.matched_dimensions


@pytest.mark.parametrize("value", [-1.0, float("nan"), float("inf")])
def test_invalid_copied_tolerance_is_rejected(value: float) -> None:
    broker = MockBrokerAdapter().snapshot()
    internal = internal_from_books(
        matching_internal_books(), observed_at=broker.provenance.source_timestamp
    )
    policy = ReconciliationTolerances().model_copy(update={"price_absolute": value})
    with pytest.raises(ValidationError):
        reconcile(broker, internal, tolerances=policy)
