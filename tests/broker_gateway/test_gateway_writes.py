from __future__ import annotations

import pytest

from quantlab.broker_gateway.errors import BrokerWriteError
from quantlab.broker_gateway.service import cancel_order, connect, modify_order, place_order
from quantlab.core.config import LiveSafetyGates
from quantlab.release.service import last_result
from quantlab.release.state import current as cert_state

pytestmark = pytest.mark.broker_gateway


def test_all_write_paths_blocked() -> None:
    connect()
    with pytest.raises(BrokerWriteError):
        place_order(symbol="TCS", qty=1)
    with pytest.raises(BrokerWriteError):
        cancel_order("BRK-ORD-1")
    with pytest.raises(BrokerWriteError):
        modify_order("BRK-ORD-1")


def test_connect_does_not_enable_live_or_certify() -> None:
    before = cert_state()
    connect()
    assert LiveSafetyGates().live_trading is False
    assert LiveSafetyGates().broker_write_enabled is False
    assert cert_state() == before
    assert last_result() is None or last_result().live_enabled is False
