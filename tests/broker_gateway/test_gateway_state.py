from __future__ import annotations

import pytest

from quantlab.broker_gateway.errors import InvalidBrokerTransition
from quantlab.broker_gateway.state import ConnectionState, current, is_healthy, transition

pytestmark = pytest.mark.broker_gateway


def test_disconnected_to_connected_path() -> None:
    assert current() is ConnectionState.DISCONNECTED
    transition(ConnectionState.CONNECTING)
    transition(ConnectionState.CONNECTED_READ_ONLY)
    assert is_healthy() is True


def test_stale_is_not_healthy() -> None:
    transition(ConnectionState.CONNECTING)
    transition(ConnectionState.CONNECTED_READ_ONLY)
    transition(ConnectionState.STALE)
    assert is_healthy() is False


def test_illegal_jump_blocked() -> None:
    with pytest.raises(InvalidBrokerTransition):
        transition(ConnectionState.CONNECTED_READ_ONLY)
