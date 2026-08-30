from pathlib import Path

import pytest

from quantlab.app.shadow import (
    audit_payload,
    health_payload,
    run_payload,
)
from quantlab.core.config import LiveSafetyGates
from quantlab.paper_oms.state import reset as reset_paper
from quantlab.shadow.enums import ShadowMode
from quantlab.shadow.state import reset as reset_shadow

pytestmark = pytest.mark.shadow


@pytest.fixture(autouse=True)
def _isolate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "quantlab.shadow.checkpoint.default_path",
        lambda: tmp_path / "shadow_checkpoint.json",
    )
    reset_shadow()
    reset_paper()
    yield
    reset_shadow()
    reset_paper()


def test_run_payload_labels_synthetic(tmp_path: Path) -> None:
    payload = run_payload(mode="research_paper", ledger=str(tmp_path / "ledger.jsonl"))
    assert payload["live_trading"] is False
    assert payload["shadow_mode"] is True
    assert payload["broker_routing_enabled"] is False
    assert payload["production_run"] is False
    assert payload["mode"] == ShadowMode.RESEARCH_PAPER.value
    assert payload["orders"] >= 1


def test_paper_and_shadow_cli_modes(tmp_path: Path) -> None:
    paper = run_payload(mode="paper", ledger=str(tmp_path / "ledger.jsonl"))
    assert paper["requested_mode"] == "paper"
    assert paper["production_run"] is False
    reset_shadow()
    reset_paper()
    shadow = run_payload(mode="shadow", ledger=str(tmp_path / "ledger.jsonl"))
    assert shadow["requested_mode"] == "shadow"
    assert shadow["live_trading"] is False


def test_health_and_audit_payloads() -> None:
    run_payload(mode="research_paper")
    health = health_payload()
    assert health["live_trading"] is False
    assert health["shadow_mode"] is True
    assert "scorecard" in health
    assert health["scorecard"]["safety"] == "pass"
    audit = audit_payload("last")
    assert audit["broker_imports"] is False
    assert audit["live_order_submission_enabled"] is False
    gates = LiveSafetyGates()
    assert gates.live_trading is False
