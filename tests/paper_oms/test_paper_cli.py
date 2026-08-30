from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from quantlab.paper_oms.cli import run_paper_command, run_research_paper_command
from quantlab.paper_oms.state import reset

pytestmark = pytest.mark.paper_oms


def test_paper_list_and_submit(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    reset()
    args = argparse.Namespace(
        paper_cmd="submit", item_id="last", policy="base", ledger=str(tmp_path / "ledger.jsonl")
    )
    assert run_paper_command(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["live_trading"] is False
    assert payload["order_count"] > 0
    assert payload["selection_stage"] == "paper_oms"
    args = argparse.Namespace(paper_cmd="list")
    assert run_paper_command(args) == 0
    rows = json.loads(capsys.readouterr().out)
    assert rows[0]["oms_run_id"] == payload["oms_run_id"]


def test_research_paper_alias(capsys: pytest.CaptureFixture[str]) -> None:
    args = argparse.Namespace(research_cmd="paper-oms", item_id="last", ledger="")
    assert run_research_paper_command(args) == 0
    rows = json.loads(capsys.readouterr().out)
    assert rows
