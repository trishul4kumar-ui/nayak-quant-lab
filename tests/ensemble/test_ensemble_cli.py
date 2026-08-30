from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from quantlab.ensemble.cli import run_ensemble_command


@pytest.mark.ensemble
def test_ensemble_cli_list_and_inspect(capsys: pytest.CaptureFixture[str]) -> None:
    assert run_ensemble_command(argparse.Namespace(ensemble_cmd="list")) == 0
    rows = json.loads(capsys.readouterr().out)
    ids = {row["ensemble_id"] for row in rows}
    assert "ew_mom_5_20" in ids
    assert "ridge_stack_mom" in ids
    args = argparse.Namespace(ensemble_cmd="inspect", item_id="ew_mom_5_20")
    assert run_ensemble_command(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["weighting_policy"] == "equal"
    assert payload["identity_hash"]


@pytest.mark.ensemble
def test_research_meta_alpha_cli(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("QUANT_LAB_DATA_DIR", str(tmp_path))
    from quantlab.research.cli import run_research_command

    args = argparse.Namespace(
        cmd="research",
        research_cmd="meta-alpha",
        ensemble_id="ew_mom_5_20",
        ledger=str(tmp_path / "ledger.jsonl"),
        n_days=80,
        lookback=20,
        top_n=2,
        cost_bps=10.0,
        family_size=1,
    )
    assert run_research_command(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["gate_outcome"] == "warn"
    assert payload["data_kind"] == "synthetic"


@pytest.mark.ensemble
def test_research_ensemble_still_prompt07(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("QUANT_LAB_DATA_DIR", str(tmp_path))
    from quantlab.research.cli import run_research_command

    args = argparse.Namespace(
        cmd="research",
        research_cmd="ensemble",
        ensemble_id="mom_5_20",
        ledger=str(tmp_path / "ledger.jsonl"),
        n_days=40,
        lookback=20,
        top_n=2,
        cost_bps=10.0,
    )
    assert run_research_command(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ensemble"]["ensemble_id"] == "mom_5_20"
    assert "ic" in payload
