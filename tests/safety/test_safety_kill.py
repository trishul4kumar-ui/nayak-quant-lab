from __future__ import annotations

from quantlab.safety.kill_switch import is_active, live_release_blocked
from quantlab.safety.models import KillScope
from quantlab.safety.service import evaluate_request, kill, unkill


def test_active_kill_switch_blocks() -> None:
    kill(KillScope.GLOBAL, reason="test")
    result = evaluate_request()
    gate = result.gate("G10_KILL_SWITCH")
    assert gate is not None
    assert gate.blocks_release
    assert result.live_release_authorized is False


def test_live_release_kill_cannot_be_cleared() -> None:
    unkill(KillScope.LIVE_RELEASE, reason="attempt")
    assert is_active(KillScope.LIVE_RELEASE)
    assert live_release_blocked()


def test_kill_never_creates_order() -> None:
    result = kill(KillScope.NEW_ORDER, reason="halt new")
    assert "broker" not in result.note.lower()
    assert result.live_trading is False
