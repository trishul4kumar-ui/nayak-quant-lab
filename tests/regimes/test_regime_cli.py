from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from quantlab.regimes.cli import run_regime_command, run_state_command


@pytest.mark.regime
def test_state_cli_list_and_inspect(capsys: pytest.CaptureFixture[str]) -> None:
    assert run_state_command(argparse.Namespace(state_cmd="list")) == 0
    rows = json.loads(capsys.readouterr().out)
    ids = {row["variable_id"] for row in rows}
    assert "realized_vol_20" in ids
    assert "index_nifty_return" in ids
    args = argparse.Namespace(state_cmd="inspect", variable_id="market_ew_return")
    assert run_state_command(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert "nifty" in payload["notes"].lower()


@pytest.mark.regime
def test_state_cli_compute(capsys: pytest.CaptureFixture[str]) -> None:
    args = argparse.Namespace(state_cmd="compute", variable_id="realized_vol_20")
    assert run_state_command(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["as_of"]
    assert payload["snapshot"]["index_nifty_return"] is None


@pytest.mark.regime
def test_regime_cli_list_and_inspect(capsys: pytest.CaptureFixture[str]) -> None:
    assert run_regime_command(argparse.Namespace(regime_cmd="list")) == 0
    rows = json.loads(capsys.readouterr().out)
    ids = {row["regime_model_id"] for row in rows}
    assert "vol_tercile" in ids
    assert "hmm_vol_smooth" in ids
    args = argparse.Namespace(regime_cmd="inspect", item_id="vol_tercile")
    assert run_regime_command(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["detector"] == "rule"


@pytest.mark.regime
def test_regime_cli_classify_and_changes(capsys: pytest.CaptureFixture[str]) -> None:
    args = argparse.Namespace(regime_cmd="classify", item_id="vol_tercile", n_days=80)
    assert run_regime_command(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["n"] > 0
    args = argparse.Namespace(regime_cmd="changes", item_id="cusum_ew", n_days=80)
    assert run_regime_command(args) == 0
    changes = json.loads(capsys.readouterr().out)
    assert "not a regime" in changes["note"].lower()


@pytest.mark.regime
def test_research_regime_cli(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("QUANT_LAB_DATA_DIR", str(tmp_path))
    from quantlab.research.cli import run_research_command

    args = argparse.Namespace(
        cmd="research",
        research_cmd="regime",
        regime_model_id="vol_tercile",
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
    assert payload["n_labelled"] > 0
