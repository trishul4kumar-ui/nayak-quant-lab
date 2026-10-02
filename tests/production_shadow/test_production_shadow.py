from __future__ import annotations

from pathlib import Path

import pytest

from quantlab.core.config import LiveSafetyGates
from quantlab.production_shadow.models import ShadowProductionState
from quantlab.production_shadow.repository import reset_for_tests
from quantlab.production_shadow.service import assess, start, stop


@pytest.fixture(autouse=True)
def _reset() -> None:
    reset_for_tests()


def test_missing_production_evidence_fails_closed_without_routing() -> None:
    result = assess()
    assert result.state is ShadowProductionState.BLOCKED
    assert result.non_routable is True
    assert result.live_trading is False
    assert result.broker_write_enabled is False
    assert "market_snapshot" in result.readiness.critical_failures
    assert LiveSafetyGates().all_pass() is False


def test_start_stop_are_assessment_state_only() -> None:
    assert start() is ShadowProductionState.RUNNING
    assert stop() is ShadowProductionState.STOPPED


def test_production_shadow_has_no_broker_write_path() -> None:
    source = "\n".join(
        item.read_text() for item in Path("src/quantlab/production_shadow").glob("*.py")
    )
    for forbidden in ("place_order", "cancel_order", "modify_order"):
        assert forbidden not in source
