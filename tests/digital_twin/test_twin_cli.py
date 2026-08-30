from __future__ import annotations

import argparse
import json

import pytest

from quantlab.digital_twin.cli import run_twin_command

pytestmark = pytest.mark.digital_twin


def test_twin_run(capsys: pytest.CaptureFixture[str]) -> None:
    args = argparse.Namespace(
        twin_cmd="run",
        item_id="last",
        mode="determinism_test",
        kind="stale_market",
    )
    assert run_twin_command(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["live_trading"] is False
    assert payload["write_enabled"] is False


def test_twin_determinism(capsys: pytest.CaptureFixture[str]) -> None:
    args = argparse.Namespace(
        twin_cmd="determinism",
        item_id="last",
        mode="determinism_test",
        kind="stale_market",
    )
    assert run_twin_command(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["match"] is True
    assert payload["live_trading"] is False


def test_twin_replay(capsys: pytest.CaptureFixture[str]) -> None:
    run_twin_command(
        argparse.Namespace(
            twin_cmd="run",
            item_id="last",
            mode="determinism_test",
            kind="stale_market",
        )
    )
    capsys.readouterr()
    args = argparse.Namespace(
        twin_cmd="replay",
        item_id="last",
        mode="determinism_test",
        kind="stale_market",
    )
    assert run_twin_command(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["live_trading"] is False
