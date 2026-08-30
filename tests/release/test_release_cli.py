from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from quantlab.release.cli import run_certification_command

pytestmark = pytest.mark.release


def test_certification_status(capsys: pytest.CaptureFixture[str]) -> None:
    args = argparse.Namespace(certification_cmd="status", item_id="last")
    assert run_certification_command(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["live_trading"] is False
    assert payload["live_enabled"] is False


def test_certification_audit(capsys: pytest.CaptureFixture[str]) -> None:
    args = argparse.Namespace(certification_cmd="audit", item_id="last")
    assert run_certification_command(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["live_trading"] is False


def test_no_broker_imports() -> None:
    root = Path("src/quantlab/release")
    banned = ("kiteconnect", "zerodha", "openalgo", "quantlab.brokers")
    for path in root.rglob("*.py"):
        text = path.read_text()
        for token in banned:
            assert token not in text
