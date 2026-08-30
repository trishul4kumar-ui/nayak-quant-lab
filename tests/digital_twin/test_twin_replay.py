from __future__ import annotations

from pathlib import Path

import pytest

from quantlab import __version__
from quantlab.core.config import LiveSafetyGates
from quantlab.digital_twin.errors import InvalidTwinTransition, TwinRoutingError
from quantlab.digital_twin.models import FailureKind, TwinMode
from quantlab.digital_twin.service import (
    inject_failure,
    place_order,
    replay,
    run_twin,
)
from quantlab.digital_twin.state import TwinState, current, transition

pytestmark = pytest.mark.digital_twin


def test_version() -> None:
    assert __version__ == "3.1.0"


def test_determinism_replay_matches() -> None:
    first = run_twin(mode=TwinMode.DETERMINISM_TEST)
    second = replay(first.run_id)
    assert first.decision_hash == second.decision_hash
    assert first.snapshot_hash == second.snapshot_hash
    assert first.fill_hash == second.fill_hash
    assert first.live_trading is False
    assert first.write_enabled is False
    assert LiveSafetyGates().live_trading is False


def test_simulated_fill_is_not_broker() -> None:
    item = run_twin()
    assert item.fill_hash
    assert item.note
    assert "BROKER" in item.note.upper() or "broker" in item.note.lower()


def test_stale_market_abstains() -> None:
    item = inject_failure(FailureKind.STALE_MARKET)
    assert item.response is not None
    assert item.decision_hash
    assert item.fill_hash == ""
    assert item.live_trading is False


def test_counterfactual_labelled() -> None:
    item = run_twin(mode=TwinMode.COUNTERFACTUAL)
    assert item.counterfactual is True
    assert "COUNTERFACTUAL" in item.extras.get("label", "")


def test_place_order_blocked() -> None:
    with pytest.raises(TwinRoutingError):
        place_order(symbol="TCS", qty=1)
    assert LiveSafetyGates().broker_write_enabled is False


def test_illegal_twin_transition() -> None:
    assert current() is TwinState.IDLE
    with pytest.raises(InvalidTwinTransition):
        transition(TwinState.SIMULATING)


def test_no_vendor_sdk_imports() -> None:
    root = Path("src/quantlab/digital_twin")
    blob = "\n".join(path.read_text() for path in root.glob("*.py"))
    for needle in ("kiteconnect", "zerodha", "openalgo", "quantlab.brokers"):
        assert needle not in blob
    decision = Path("src/quantlab/realtime_decision")
    blob2 = "\n".join(path.read_text() for path in decision.glob("*.py"))
    for needle in ("kiteconnect", "zerodha", "openalgo"):
        assert needle not in blob2
