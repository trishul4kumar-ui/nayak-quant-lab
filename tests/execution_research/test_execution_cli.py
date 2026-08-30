from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from quantlab.execution_research.cli import run_execution_command


@pytest.mark.execution_research
def test_execution_cli_list_and_inspect(capsys: pytest.CaptureFixture[str]) -> None:
    assert run_execution_command(argparse.Namespace(execution_cmd="list")) == 0
    rows = json.loads(capsys.readouterr().out)
    ids = {row["definition_id"] for row in rows}
    assert "exec_base" in ids
    assert "exec_zero_cost" in ids
    args = argparse.Namespace(execution_cmd="inspect", item_id="exec_base")
    assert run_execution_command(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["definition_id"] == "exec_base"
    assert payload["identity_hash"]
    assert "OMS" in payload["note"]


@pytest.mark.execution_research
def test_execution_cli_simulate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("QUANT_LAB_DATA_DIR", str(tmp_path))
    args = argparse.Namespace(
        execution_cmd="simulate",
        item_id="exec_base",
        ledger=str(tmp_path / "ledger.jsonl"),
        n_days=80,
        family_size=1,
        capital=1_000_000.0,
        scenario="",
    )
    assert run_execution_command(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["gate_outcome"] == "warn"
    assert payload["data_kind"] == "synthetic"
    assert payload["live_trading"] is False
    assert payload["total_cost"] > 0


@pytest.mark.execution_research
def test_research_execution_cli(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("QUANT_LAB_DATA_DIR", str(tmp_path))
    from quantlab.research.cli import run_research_command

    args = argparse.Namespace(
        cmd="research",
        research_cmd="execution",
        model_id="exec_base",
        ledger=str(tmp_path / "ledger.jsonl"),
        n_days=80,
        lookback=20,
        top_n=2,
        cost_bps=10.0,
    )
    assert run_research_command(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["gate_outcome"] == "warn"
    assert payload["execution_model_id"] == "exec_base"
