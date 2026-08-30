from __future__ import annotations

import argparse
import json

import pytest

from quantlab.knowledge.cli import run_knowledge_command, run_research_knowledge_command

pytestmark = pytest.mark.knowledge


def test_knowledge_list_cli(capsys: pytest.CaptureFixture[str]) -> None:
    args = argparse.Namespace(knowledge_cmd="list")
    assert run_knowledge_command(args) == 0
    rows = json.loads(capsys.readouterr().out)
    ids = {row["node_id"] for row in rows}
    assert "hypothesis:H-MOM-001" in ids
    assert "dead-end:DEAD_END-042" in ids


def test_knowledge_report_cli(capsys: pytest.CaptureFixture[str]) -> None:
    args = argparse.Namespace(knowledge_cmd="report", hypothesis_id="H-MOM-001")
    assert run_knowledge_command(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["live_trading"] is False
    assert "WHAT" in payload


def test_research_dead_ends_alias(capsys: pytest.CaptureFixture[str]) -> None:
    args = argparse.Namespace(research_cmd="dead-ends", item_id="H-MOM-001")
    assert run_research_knowledge_command(args) == 0
    rows = json.loads(capsys.readouterr().out)
    assert any(row["node_id"] == "dead-end:DEAD_END-042" for row in rows)
