from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from quantlab.adaptive.cli import run_adaptive_command


@pytest.mark.adaptive
def test_adaptive_cli_list_and_inspect(capsys: pytest.CaptureFixture[str]) -> None:
    assert run_adaptive_command(argparse.Namespace(adaptive_cmd="list")) == 0
    rows = json.loads(capsys.readouterr().out)
    ids = {row["adaptive_model_id"] for row in rows}
    assert "static_mom20" in ids
    assert "ensemble_ic_mom" in ids
    args = argparse.Namespace(adaptive_cmd="inspect", item_id="static_mom20")
    assert run_adaptive_command(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["policy"] == "no_adaptation"
    assert payload["identity_hash"]


@pytest.mark.adaptive
def test_adaptive_cli_decay(capsys: pytest.CaptureFixture[str]) -> None:
    args = argparse.Namespace(adaptive_cmd="decay", alpha_id="rank_momentum_20")
    assert run_adaptive_command(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["method"] == "linear_ols"
    assert payload["status"] in {"estimable", "insufficient_data", "unstable", "not_tested"}


@pytest.mark.adaptive
def test_research_adaptive_cli(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("QUANT_LAB_DATA_DIR", str(tmp_path))
    from quantlab.research.cli import run_research_command

    args = argparse.Namespace(
        cmd="research",
        research_cmd="adaptive",
        adaptive_model_id="static_mom20",
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
