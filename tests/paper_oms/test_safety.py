from __future__ import annotations

from pathlib import Path

import pytest

from quantlab.paper_oms.errors import PaperSafetyError
from quantlab.paper_oms.safety import FORBIDDEN_CREDENTIAL_VARS, assert_paper_only

pytestmark = pytest.mark.paper_oms


def test_credentials_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_SECRET", "not-a-real-secret")
    with pytest.raises(PaperSafetyError):
        assert_paper_only()


def test_broker_imports_absent() -> None:
    root = Path(__file__).resolve().parents[2] / "src" / "quantlab" / "paper_oms"
    banned = ("kiteconnect", "zerodha", "openalgo", "quantlab.brokers")
    for path in root.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{path.name} contains {token}"


def test_forbidden_names_documented() -> None:
    assert "API_SECRET" in FORBIDDEN_CREDENTIAL_VARS
    assert "LIVE_ACCOUNT_ID" in FORBIDDEN_CREDENTIAL_VARS
