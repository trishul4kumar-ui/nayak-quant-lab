from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from quantlab.portfolio.cli import run_portfolio_command


@pytest.mark.portfolio
def test_portfolio_cli_list_and_inspect(capsys: pytest.CaptureFixture[str]) -> None:
    args = argparse.Namespace(portfolio_cmd="list")
    assert run_portfolio_command(args) == 0
    payload = json.loads(capsys.readouterr().out)
    ids = {row["portfolio_id"] for row in payload["portfolios"]}
    assert "mom20_topn" in ids
    assert "mom20_minvar" in ids
    args = argparse.Namespace(portfolio_cmd="inspect", item_id="mom20_topn")
    assert run_portfolio_command(args) == 0
    model = json.loads(capsys.readouterr().out)
    assert model["constructor"] == "top_n"


@pytest.mark.portfolio
def test_portfolio_cli_build(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("QUANT_LAB_DATA_DIR", str(tmp_path))
    args = argparse.Namespace(
        portfolio_cmd="build",
        item_id="mom20_topn",
        ledger=str(tmp_path / "ledger.jsonl"),
        n_days=80,
        family_size=1,
    )
    assert run_portfolio_command(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["gate_outcome"] == "warn"
    assert payload["data_kind"] == "synthetic"
    assert payload["infeasible"] is False
    assert payload["n_rebalances"] > 10
