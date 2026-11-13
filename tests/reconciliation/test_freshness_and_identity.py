from __future__ import annotations

from datetime import timedelta
from threading import Event, Thread

import pytest

from quantlab.broker_gateway.mock import MockBrokerAdapter
from quantlab.broker_gateway.service import matching_internal_books
from quantlab.reconciliation.models import ReconciliationStatus, ReconciliationTolerances
from quantlab.reconciliation.repository import get, reset_for_tests
from quantlab.reconciliation.service import internal_from_books, reconcile


@pytest.fixture(autouse=True)
def _clear() -> None:
    reset_for_tests()


def test_equal_but_old_snapshots_do_not_claim_a_current_match() -> None:
    broker = MockBrokerAdapter().snapshot()
    internal = internal_from_books(
        matching_internal_books(), observed_at=broker.provenance.source_timestamp
    )
    report = reconcile(
        broker,
        internal,
        observed_at=broker.provenance.source_timestamp + timedelta(seconds=61),
        tolerances=ReconciliationTolerances(max_snapshot_age_seconds=60),
    )
    assert report.status is ReconciliationStatus.STALE
    assert report.matched_dimensions == ()


def test_future_and_naive_source_timestamps_fail_closed() -> None:
    broker = MockBrokerAdapter().snapshot()
    internal = internal_from_books(
        matching_internal_books(), observed_at=broker.provenance.source_timestamp
    )
    now = broker.provenance.source_timestamp
    for timestamp in (now + timedelta(seconds=1), now.replace(tzinfo=None)):
        changed = broker.model_copy(update={
            "provenance": broker.provenance.model_copy(update={"source_timestamp": timestamp})
        })
        assert reconcile(changed, internal, observed_at=now).status is ReconciliationStatus.STALE


def test_reversed_or_missing_capture_window_is_stale() -> None:
    broker = MockBrokerAdapter().snapshot()
    internal = internal_from_books(
        matching_internal_books(), observed_at=broker.provenance.source_timestamp
    )
    now = broker.provenance.source_timestamp
    for started, ended in ((now, now - timedelta(seconds=1)), (None, now)):
        changed = broker.model_copy(update={
            "capture_started_at": started, "capture_completed_at": ended
        })
        assert reconcile(changed, internal, observed_at=now).status is ReconciliationStatus.STALE


def test_reconciliation_hash_binds_actual_snapshot_contents() -> None:
    broker = MockBrokerAdapter().snapshot()
    internal = internal_from_books(
        matching_internal_books(), observed_at=broker.provenance.source_timestamp
    )
    first = reconcile(broker, internal)
    # IDs remain unchanged; both independently provided cash values change equally.
    changed_broker = broker.model_copy(update={
        "account": broker.account.model_copy(update={"available_cash": 100001.0})
    })
    changed_internal = internal.model_copy(update={"available_cash": 100001.0})
    second = reconcile(changed_broker, changed_internal)
    assert first.status is second.status is ReconciliationStatus.MATCH
    assert first.reconciliation_hash != second.reconciliation_hash
    assert first.broker_snapshot_content_hash != second.broker_snapshot_content_hash
    assert first.internal_snapshot_content_hash != second.internal_snapshot_content_hash


def test_latest_report_lookup_does_not_deadlock() -> None:
    broker = MockBrokerAdapter().snapshot()
    internal = internal_from_books(
        matching_internal_books(), observed_at=broker.provenance.source_timestamp
    )
    report = reconcile(broker, internal)
    finished = Event()
    result: list[object] = []

    def lookup() -> None:
        result.append(get("last"))
        finished.set()

    Thread(target=lookup, daemon=True).start()
    assert finished.wait(2.0), "latest reconciliation lookup deadlocked"
    assert result == [report]
