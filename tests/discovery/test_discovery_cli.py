from __future__ import annotations

import argparse
import json

import pytest

from quantlab.discovery.cli import run_discovery_command


@pytest.mark.discovery
def test_discovery_list_cli(capsys: pytest.CaptureFixture[str]) -> None:
    assert run_discovery_command(argparse.Namespace(discovery_cmd="list")) == 0
    rows = json.loads(capsys.readouterr().out)
    ids = {row["family_id"] for row in rows}
    assert "GP-MOM-VOL-001" in ids


@pytest.mark.discovery
def test_discovery_inspect_cli(capsys: pytest.CaptureFixture[str]) -> None:
    args = argparse.Namespace(discovery_cmd="inspect", family_id="GP-MOM-VOL-001")
    assert run_discovery_command(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert "rank(momentum_20)" in payload["seeds"]
    assert payload["family_id"] == "GP-MOM-VOL-001"
