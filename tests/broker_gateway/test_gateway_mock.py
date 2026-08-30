from __future__ import annotations

from pathlib import Path

import pytest

from quantlab import __version__
from quantlab.broker_gateway.errors import BrokerGatewayError, BrokerWriteError
from quantlab.broker_gateway.mock import MockBrokerAdapter
from quantlab.broker_gateway.models import MockScenario
from quantlab.broker_gateway.protocol import BrokerAdapter
from quantlab.broker_gateway.service import (
    connect,
    health,
    last_snapshot,
    matching_internal_books,
    place_order,
    reconcile,
    snapshot,
)
from quantlab.core.config import LiveSafetyGates

pytestmark = pytest.mark.broker_gateway


def test_version_and_flags() -> None:
    assert __version__ == "3.1.0"
    assert LiveSafetyGates().live_trading is False
    assert LiveSafetyGates().broker_write_enabled is False


def test_mock_is_protocol() -> None:
    adapter = MockBrokerAdapter()
    assert isinstance(adapter, BrokerAdapter)


def test_connect_read_only() -> None:
    item = connect()
    assert item.healthy is True
    assert item.live_trading is False
    assert item.write_enabled is False
    assert health().state == "connected_read_only"


def test_snapshot_is_hashed_and_idempotent() -> None:
    connect()
    first = snapshot()
    second = snapshot()
    assert first.payload_hash == second.payload_hash
    assert first.account.payload_hash
    assert last_snapshot() is not None


def test_write_attempts_fail_closed() -> None:
    connect()
    with pytest.raises(BrokerWriteError):
        place_order()
    with pytest.raises(BrokerWriteError):
        MockBrokerAdapter().place_order()


def test_connection_failure() -> None:
    with pytest.raises(BrokerGatewayError):
        connect(MockScenario.CONNECTION_FAILURE)


def test_stale_snapshot_not_healthy() -> None:
    item = connect(MockScenario.STALE_SNAPSHOT)
    assert item.stale is True
    assert item.healthy is False


def test_aligned_recon_is_reconciled() -> None:
    connect()
    snapshot()
    result = reconcile(matching_internal_books())
    assert result.status.value == "reconciled"
    assert result.live_trading is False
    assert result.write_enabled is False


def test_empty_internal_does_not_invent_orders() -> None:
    connect()
    snapshot()
    result = reconcile()
    assert result.unknown_broker_orders
    assert result.status.value == "blocked"


def test_no_banned_imports() -> None:
    root = Path("src/quantlab/broker_gateway")
    banned = ("kiteconnect", "zerodha", "openalgo", "quantlab.brokers")
    for path in root.rglob("*.py"):
        text = path.read_text()
        for token in banned:
            assert token not in text
