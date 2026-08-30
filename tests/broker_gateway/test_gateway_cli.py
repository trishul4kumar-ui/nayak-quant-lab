from __future__ import annotations

import argparse
import json

import pytest

from quantlab.broker_gateway.cli import run_broker_command

pytestmark = pytest.mark.broker_gateway


def test_broker_health(capsys: pytest.CaptureFixture[str]) -> None:
    args = argparse.Namespace(broker_cmd="health", item_id="last", scenario="normal")
    assert run_broker_command(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["live_trading"] is False
    assert payload["write_enabled"] is False


def test_broker_snapshot(capsys: pytest.CaptureFixture[str]) -> None:
    args = argparse.Namespace(broker_cmd="snapshot", item_id="last", scenario="normal")
    assert run_broker_command(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["live_trading"] is False
    assert payload["write_enabled"] is False
    assert "payload_hash" in payload
