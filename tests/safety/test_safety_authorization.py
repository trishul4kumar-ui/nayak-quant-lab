from __future__ import annotations

from pathlib import Path

import pytest

from quantlab import __version__
from quantlab.core.config import LiveSafetyGates
from quantlab.safety.errors import AuthorizationError, ReleaseBlocked
from quantlab.safety.models import SafetyRequest
from quantlab.safety.service import authorize


def test_live_trading_false_cannot_authorize_live_release() -> None:
    assert LiveSafetyGates().live_trading is False
    with pytest.raises(ReleaseBlocked):
        authorize(SafetyRequest(live_release=True))


def test_mutated_target_invalidates_authorization() -> None:
    with pytest.raises(AuthorizationError):
        authorize(SafetyRequest(mutated_target=True, live_release=False))


def test_authorization_is_not_live() -> None:
    result = authorize(SafetyRequest(live_release=False, human_approval_id=""))
    assert result.live_release_authorized is False
    assert result.authorization is not None
    assert result.authorization.live_release is False
    assert result.authorization.release_allowed is False
    assert result.blocked is True


def test_version() -> None:
    assert __version__ == "3.1.0"


def test_no_broker_imports() -> None:
    root = Path("src/quantlab/safety")
    banned = ("kiteconnect", "zerodha", "openalgo", "quantlab.brokers")
    for path in root.rglob("*.py"):
        text = path.read_text()
        for token in banned:
            assert token not in text
