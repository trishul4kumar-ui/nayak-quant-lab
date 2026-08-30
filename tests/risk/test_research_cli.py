from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from quantlab.risk.cli import run_risk_command


@pytest.mark.factor
def test_risk_cli_list_and_inspect(capsys: pytest.CaptureFixture[str]) -> None:
    assert run_risk_command(argparse.Namespace(risk_cmd="list")) == 0
    rows = json.loads(capsys.readouterr().out)
    ids = {row["risk_model_id"] for row in rows}
    assert "sample_cs" in ids
    assert "ewma_cs" in ids
    args = argparse.Namespace(risk_cmd="inspect", item_id="sample_cs")
    assert run_risk_command(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["benchmark"] == "equal_weight_universe"


@pytest.mark.factor
def test_risk_cli_compute(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("QUANT_LAB_DATA_DIR", str(tmp_path))
    args = argparse.Namespace(
        risk_cmd="compute",
        portfolio="mom20_topn",
        ledger=str(tmp_path / "ledger.jsonl"),
        n_days=80,
        family_size=1,
        model="sample_cs",
    )
    assert run_risk_command(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["gate_outcome"] == "warn"
    assert payload["data_kind"] == "synthetic"
    assert payload["psd"] is True
    experiment_id = payload["experiment_id"]
    args = argparse.Namespace(
        risk_cmd="stress",
        experiment=experiment_id,
        ledger=str(tmp_path / "ledger.jsonl"),
    )
    assert run_risk_command(args) == 0
    stress = json.loads(capsys.readouterr().out)
    assert isinstance(stress, list)
    assert "not a forecast" in stress[0]["note"]
