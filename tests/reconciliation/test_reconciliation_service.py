from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pytest

from quantlab.broker_gateway.mock import MockBrokerAdapter
from quantlab.broker_gateway.service import matching_internal_books
from quantlab.reconciliation.models import (
    ExceptionStatus,
    ReconciliationStatus,
    ReconciliationTolerances,
)
from quantlab.reconciliation.repository import exceptions, reset_for_tests
from quantlab.reconciliation.service import internal_from_books, reconcile, transition_exception


@pytest.fixture(autouse=True)
def _reset() -> None:
    reset_for_tests()


def test_exact_mock_reconciliation_is_deterministic() -> None:
    broker = MockBrokerAdapter().snapshot()
    internal = internal_from_books(
        matching_internal_books(), observed_at=broker.provenance.source_timestamp
    )
    first = reconcile(broker, internal)
    second = reconcile(broker, internal)
    assert first.status is ReconciliationStatus.MATCH
    assert first.reconciliation_hash == second.reconciliation_hash
    assert first is second


def test_explicit_cash_tolerance_is_recorded() -> None:
    broker = MockBrokerAdapter().snapshot()
    internal = internal_from_books(
        matching_internal_books(), observed_at=broker.provenance.source_timestamp
    )
    internal = internal.model_copy(update={"available_cash": 100_000.005})
    report = reconcile(broker, internal, tolerances=ReconciliationTolerances(cash_absolute=0.01))
    assert report.status is ReconciliationStatus.MATCH_WITH_TOLERANCE
    assert "cash" in report.tolerance_dimensions


def test_unknown_fill_is_a_critical_break_and_can_only_follow_fsm() -> None:
    broker = MockBrokerAdapter().snapshot()
    internal = internal_from_books(
        matching_internal_books(), observed_at=broker.provenance.source_timestamp
    )
    internal = internal.model_copy(update={"fills": ()})
    report = reconcile(broker, internal)
    assert report.status is ReconciliationStatus.RECONCILIATION_BREAK
    item = next(row for row in exceptions() if row.dimension == "fill")
    acknowledged = transition_exception(item, ExceptionStatus.ACKNOWLEDGED)
    investigating = transition_exception(acknowledged, ExceptionStatus.INVESTIGATING)
    assert (
        transition_exception(investigating, ExceptionStatus.RESOLVED).status
        is ExceptionStatus.RESOLVED
    )
    with pytest.raises(ValueError):
        transition_exception(item, ExceptionStatus.RESOLVED)


def test_stale_snapshots_never_become_match() -> None:
    broker = MockBrokerAdapter().snapshot()
    internal = internal_from_books(
        matching_internal_books(),
        observed_at=broker.provenance.source_timestamp + timedelta(seconds=6),
    )
    report = reconcile(broker, internal, tolerances=ReconciliationTolerances(timestamp_seconds=5.0))
    assert report.status is ReconciliationStatus.STALE


def test_reconciliation_has_no_broker_write_path() -> None:
    root = Path("src/quantlab/reconciliation")
    source = "\n".join(item.read_text() for item in root.glob("*.py"))
    for forbidden in ("place_order", "cancel_order", "modify_order"):
        assert forbidden not in source
