from __future__ import annotations

import pytest

from quantlab.broker_gateway.audit import history, record
from quantlab.broker_gateway.secrets import account_id_hash, redact

pytestmark = pytest.mark.broker_gateway


def test_credentials_are_redacted() -> None:
    assert redact("super-secret") == "***REDACTED***"
    assert account_id_hash("mock-account") != "mock-account"
    record({"event": "connect", "api_key": "should-not-leak", "live_trading": False})
    row = history()[-1]
    assert row["api_key"] == "***REDACTED***"
    assert "should-not-leak" not in str(row)
