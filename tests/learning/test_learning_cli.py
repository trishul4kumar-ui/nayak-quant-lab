from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from quantlab.learning.cli import run_model_command


@pytest.mark.learning
def test_model_cli_list_and_inspect(capsys: pytest.CaptureFixture[str]) -> None:
    assert run_model_command(argparse.Namespace(model_cmd="list")) == 0
    rows = json.loads(capsys.readouterr().out)
    ids = {row["model_id"] for row in rows}
    assert "ols_mom" in ids
    assert "rf_mom" in ids
    args = argparse.Namespace(model_cmd="inspect", item_id="ols_mom")
    assert run_model_command(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["algorithm"] == "ols"
    assert payload["identity_hash"]


@pytest.mark.learning
def test_research_model_cli(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("QUANT_LAB_DATA_DIR", str(tmp_path))
    from quantlab.research.cli import run_research_command

    args = argparse.Namespace(
        cmd="research",
        research_cmd="model",
        model_id="ols_mom",
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
