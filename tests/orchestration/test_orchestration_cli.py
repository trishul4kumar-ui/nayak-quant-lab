from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from quantlab.orchestration.cli import (
    run_experiment_command,
    run_hypothesis_command,
    run_research_orchestration_command,
)


@pytest.mark.orchestration
def test_hypothesis_cli_list_and_inspect(capsys: pytest.CaptureFixture[str]) -> None:
    assert run_hypothesis_command(argparse.Namespace(hypothesis_cmd="list")) == 0
    rows = json.loads(capsys.readouterr().out)
    ids = {row["hypothesis_id"] for row in rows}
    assert "H-MOM-001" in ids
    args = argparse.Namespace(hypothesis_cmd="inspect", item_id="H-MOM-001")
    assert run_hypothesis_command(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["hypothesis_id"] == "H-MOM-001"
    assert payload["identity_hash"]


@pytest.mark.orchestration
def test_experiment_cli_plan(capsys: pytest.CaptureFixture[str]) -> None:
    args = argparse.Namespace(experiment_cmd="plan", item_id="EXP-MOM-001")
    assert run_experiment_command(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["experiment_id"] == "EXP-MOM-001"


@pytest.mark.orchestration
def test_research_discover_cli(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("QUANT_LAB_DATA_DIR", str(tmp_path))
    args = argparse.Namespace(
        research_cmd="discover",
        hypothesis_id="H-MOM-001",
        experiment="EXP-MOM-001",
        ledger=str(tmp_path / "ledger.jsonl"),
        n_days=80,
    )
    assert run_research_orchestration_command(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["gate_outcome"] in {"warn", "reject"}
    assert payload["live_trading"] is False
    assert payload["attempted"] >= 4


@pytest.mark.orchestration
def test_research_status_cli(capsys: pytest.CaptureFixture[str]) -> None:
    args = argparse.Namespace(research_cmd="status")
    assert run_research_orchestration_command(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["hypotheses"] >= 1
    assert payload["live_trading"] is False
