from __future__ import annotations

import pytest

from quantlab.broker_gateway.mock import MockBrokerAdapter
from quantlab.broker_gateway.models import InternalBooks, MockScenario
from quantlab.broker_gateway.reconcile import reconcile
from quantlab.broker_gateway.service import connect, matching_internal_books, snapshot

pytestmark = pytest.mark.broker_gateway


def test_position_mismatch() -> None:
    adapter = MockBrokerAdapter(MockScenario.POSITION_MISMATCH)
    bundle = adapter.snapshot()
    result = reconcile(bundle, matching_internal_books())
    kinds = {item.kind for item in result.breaks}
    assert "position_reconciliation_break" in kinds
    assert result.status.value == "mismatch"


def test_cash_mismatch() -> None:
    adapter = MockBrokerAdapter(MockScenario.CASH_MISMATCH)
    result = reconcile(adapter.snapshot(), matching_internal_books())
    kinds = {item.kind for item in result.breaks}
    assert "cash_reconciliation_break" in kinds


def test_orphan_fill() -> None:
    adapter = MockBrokerAdapter(MockScenario.ORPHAN_FILL)
    result = reconcile(adapter.snapshot(), matching_internal_books())
    assert result.orphan_fills
    assert result.status.value == "blocked"


def test_unknown_order() -> None:
    adapter = MockBrokerAdapter(MockScenario.UNKNOWN_ORDER)
    result = reconcile(adapter.snapshot(), matching_internal_books())
    assert "BRK-ORD-UNK" in result.unknown_broker_orders
    assert result.status.value == "blocked"


def test_duplicate_fill() -> None:
    adapter = MockBrokerAdapter(MockScenario.DUPLICATE_FILL)
    result = reconcile(adapter.snapshot(), matching_internal_books())
    kinds = {item.kind for item in result.breaks}
    assert "duplicate_external_event" in kinds


def test_mapping_ambiguity_fails_closed() -> None:
    adapter = MockBrokerAdapter(MockScenario.MAPPING_AMBIGUITY)
    result = reconcile(adapter.snapshot(), matching_internal_books())
    kinds = {item.kind for item in result.breaks}
    assert "instrument_mapping_ambiguity" in kinds


def test_out_of_order_events() -> None:
    adapter = MockBrokerAdapter(MockScenario.OUT_OF_ORDER)
    result = reconcile(adapter.snapshot(), matching_internal_books())
    kinds = {item.kind for item in result.breaks}
    assert "event_ordering_failure" in kinds


def test_reconnect_does_not_erase_snapshot() -> None:
    connect()
    first = snapshot()
    from quantlab.broker_gateway.service import disconnect

    disconnect()
    connect()
    second = snapshot()
    from quantlab.broker_gateway.repository import list_bundles

    assert len(list_bundles()) >= 1
    assert first.bundle_id == second.bundle_id


def test_never_invents_internal_position() -> None:
    adapter = MockBrokerAdapter()
    result = reconcile(adapter.snapshot(), InternalBooks())
    kinds = {item.kind for item in result.breaks}
    assert "position_reconciliation_break" in kinds
    assert result.status.value != "reconciled"
