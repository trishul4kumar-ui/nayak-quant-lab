from __future__ import annotations

import argparse
import json

import pytest

from quantlab.ops.cli import run_ops_command

pytestmark = pytest.mark.ops


def test_ops_doctor(capsys: pytest.CaptureFixture[str]) -> None:
    args = argparse.Namespace(ops_cmd="doctor", name="app", backup_id="", dest="")
    assert run_ops_command(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["live_trading"] is False


def test_ops_health(capsys: pytest.CaptureFixture[str]) -> None:
    args = argparse.Namespace(ops_cmd="health", name="app", backup_id="", dest="")
    assert run_ops_command(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["live_trading"] is False
