from __future__ import annotations

import argparse
import json

import pytest

from quantlab.realtime_decision.cli import run_realtime_decision_command

pytestmark = pytest.mark.realtime_decision


def test_status(capsys: pytest.CaptureFixture[str]) -> None:
    args = argparse.Namespace(
        realtime_decision_cmd="status",
        item_id="last",
        release="default",
    )
    assert run_realtime_decision_command(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["live_trading"] is False


def test_run_default_abstains(capsys: pytest.CaptureFixture[str]) -> None:
    args = argparse.Namespace(
        realtime_decision_cmd="run",
        item_id="last",
        release="default",
    )
    assert run_realtime_decision_command(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["live_trading"] is False
    assert payload["state"] == "abstained"


def test_run_research_decides(capsys: pytest.CaptureFixture[str]) -> None:
    args = argparse.Namespace(
        realtime_decision_cmd="run",
        item_id="last",
        release="research",
    )
    assert run_realtime_decision_command(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["state"] == "decided"
    assert payload["live_trading"] is False
