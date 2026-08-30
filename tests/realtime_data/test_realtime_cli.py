from __future__ import annotations

import argparse
import json

import pytest

from quantlab.realtime_data.cli import run_realtime_command

pytestmark = pytest.mark.realtime_data


def test_realtime_health(capsys: pytest.CaptureFixture[str]) -> None:
    args = argparse.Namespace(realtime_cmd="health", item_id="last", scenario="normal")
    assert run_realtime_command(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["live_trading"] is False
    assert payload["write_enabled"] is False


def test_realtime_snapshot(capsys: pytest.CaptureFixture[str]) -> None:
    args = argparse.Namespace(realtime_cmd="snapshot", item_id="last", scenario="normal")
    assert run_realtime_command(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["live_trading"] is False
    assert payload["snapshot_hash"]
