from __future__ import annotations

import pytest

from quantlab.broker_gateway.contract import VendorReadOnlyContract
from quantlab.broker_gateway.errors import BrokerGatewayError
from quantlab.broker_gateway.repository import put_bundle
from quantlab.broker_gateway.service import connect, snapshot
from quantlab.core.config import LiveSafetyGates
from quantlab.safety.kill_switch import live_release_blocked

pytestmark = pytest.mark.broker_gateway


def test_vendor_contract_not_enabled() -> None:
    with pytest.raises(BrokerGatewayError):
        VendorReadOnlyContract().connect()


def test_payload_collision_is_integrity_failure() -> None:
    connect()
    bundle = snapshot()
    mutated = bundle.model_copy(update={"payload_hash": "mutated-hash"})
    with pytest.raises(BrokerGatewayError):
        put_bundle(mutated)


def test_kill_switch_still_blocks_live() -> None:
    connect()
    assert live_release_blocked() is True
    assert LiveSafetyGates().live_trading is False
