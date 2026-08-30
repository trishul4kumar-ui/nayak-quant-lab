from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from quantlab.capital.cli import run_capital_command, run_research_capital_command

pytestmark = pytest.mark.capital


def test_capital_list_cli(capsys: pytest.CaptureFixture[str]) -> None:
    args = argparse.Namespace(capital_cmd="list")
    assert run_capital_command(args) == 0
    rows = json.loads(capsys.readouterr().out)
    assert rows[0]["policy_id"] == "CAP-RESEARCH-001"


def test_capital_allocate_and_decision(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    ledger = str(tmp_path / "ledger.jsonl")
    args = argparse.Namespace(capital_cmd="allocate", item_id="mom20_topn", ledger=ledger)
    assert run_capital_command(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["live_trading"] is False
    assert payload["selection_stage"] == "capital_allocation"
    assert payload["weights"]
    args = argparse.Namespace(capital_cmd="decision", item_id=payload["decision_id"])
    assert run_capital_command(args) == 0
    decision = json.loads(capsys.readouterr().out)
    assert decision["decision_id"] == payload["decision_id"]


def test_research_capital_alias(capsys: pytest.CaptureFixture[str]) -> None:
    args = argparse.Namespace(research_cmd="capital", item_id="last", ledger="")
    assert run_research_capital_command(args) == 0
    rows = json.loads(capsys.readouterr().out)
    assert rows[0]["policy_id"] == "CAP-RESEARCH-001"


def test_capital_package_has_no_broker_imports() -> None:
    root = Path(__file__).resolve().parents[2] / "src" / "quantlab" / "capital"
    banned = ("kiteconnect", "import zerodha", "import openalgo", "from quantlab.brokers")
    for path in root.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{path.name} contains {token}"
