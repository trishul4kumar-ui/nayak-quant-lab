from __future__ import annotations

from pathlib import Path

import pytest

from quantlab import __version__
from quantlab.core.config import LiveSafetyGates
from quantlab.realtime_data.errors import InvalidFeedTransition
from quantlab.realtime_data.freeze import freeze
from quantlab.realtime_data.mock import SEED_AS_OF, seed_observations
from quantlab.realtime_data.models import MockFeedScenario, QualityStatus
from quantlab.realtime_data.service import health, replay, snapshot, start
from quantlab.realtime_data.state import FeedState, current, transition

pytestmark = pytest.mark.realtime_data


def test_version() -> None:
    assert __version__ == "3.1.0"


def test_snapshot_is_frozen_and_observe_only() -> None:
    start()
    frozen = snapshot()
    assert frozen.live_trading is False
    assert frozen.quality is QualityStatus.VALID
    assert frozen.n_names == 2
    mutated = frozen.append_future_data(seed_observations())
    assert mutated.snapshot_hash == frozen.snapshot_hash
    assert LiveSafetyGates().live_trading is False
    assert LiveSafetyGates().broker_write_enabled is False


def test_future_ticks_do_not_mutate_snapshot() -> None:
    rows = seed_observations()
    frozen = freeze(rows, as_of=SEED_AS_OF)
    assert frozen.append_future_data("later") is frozen
    assert freeze(rows, as_of=SEED_AS_OF).snapshot_hash == frozen.snapshot_hash


def test_stale_is_not_valid() -> None:
    start(MockFeedScenario.STALE)
    frozen = snapshot()
    assert frozen.quality is QualityStatus.STALE
    assert frozen.quality is not QualityStatus.VALID


def test_malformed_is_invalid() -> None:
    start(MockFeedScenario.MALFORMED)
    frozen = snapshot()
    assert frozen.quality is QualityStatus.INVALID


def test_replay_matches() -> None:
    start()
    original = snapshot()
    replayed = replay()
    assert replayed.snapshot_hash == original.snapshot_hash


def test_illegal_feed_transition() -> None:
    assert current() is FeedState.DISCONNECTED
    with pytest.raises(InvalidFeedTransition):
        transition(FeedState.CONNECTED)


def test_health_unknown_is_not_healthy() -> None:
    item = health()
    assert item.live_trading is False
    assert item.write_enabled is False


def test_no_vendor_sdk_imports() -> None:
    root = Path("src/quantlab/realtime_data")
    blob = "\n".join(path.read_text() for path in root.glob("*.py"))
    for needle in ("kiteconnect", "zerodha", "openalgo", "quantlab.brokers"):
        assert needle not in blob
