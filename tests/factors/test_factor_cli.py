from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from quantlab.factors.cli import run_factor_command


@pytest.mark.factor
def test_factor_cli_list_and_inspect(capsys: pytest.CaptureFixture[str]) -> None:
    assert run_factor_command(argparse.Namespace(factor_cmd="list")) == 0
    rows = json.loads(capsys.readouterr().out)
    ids = {row["factor_id"] for row in rows}
    assert "market_ew_beta" in ids
    assert "size_log_cap" in ids
    args = argparse.Namespace(factor_cmd="inspect", factor_id="market_ew_beta")
    assert run_factor_command(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["source"] == "equal_weight_market_beta"
    assert payload["known_limitations"]


@pytest.mark.factor
def test_factor_cli_compute(capsys: pytest.CaptureFixture[str]) -> None:
    args = argparse.Namespace(factor_cmd="compute", factor_id="style_momentum_20")
    assert run_factor_command(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["n_dates"] > 0
    assert payload["status"] == "pass"


@pytest.mark.factor
def test_factor_cli_not_implemented(capsys: pytest.CaptureFixture[str]) -> None:
    args = argparse.Namespace(factor_cmd="compute", factor_id="value_book_to_market")
    assert run_factor_command(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "not_tested"
    assert payload["n_dates"] == 0


@pytest.mark.factor
def test_research_factor_cli(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("QUANT_LAB_DATA_DIR", str(tmp_path))
    from quantlab.research.cli import run_research_command

    args = argparse.Namespace(
        cmd="research",
        research_cmd="factor",
        factor_id="style_momentum_20",
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
