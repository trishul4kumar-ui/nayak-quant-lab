from __future__ import annotations

import argparse
import json

import pytest

from quantlab.safety.cli import run_safety_command

pytestmark = pytest.mark.safety


def test_safety_status(capsys: pytest.CaptureFixture[str]) -> None:
    args = argparse.Namespace(safety_cmd="status", item_id="last", scope="global")
    assert run_safety_command(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["live_trading"] is False
    assert payload["live_release_authorized"] is False
    assert payload["g15"] == "block"


def test_safety_audit(capsys: pytest.CaptureFixture[str]) -> None:
    args = argparse.Namespace(safety_cmd="audit", item_id="last", scope="global")
    assert run_safety_command(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["live_trading"] is False
