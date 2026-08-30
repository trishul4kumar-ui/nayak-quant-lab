from pathlib import Path

import pytest

from quantlab.research.pipeline import run_momentum_vertical_slice


@pytest.mark.vertical_slice
def test_momentum_vertical_slice(tmp_ledger: Path) -> None:
    result, run = run_momentum_vertical_slice(ledger_path=tmp_ledger)
    assert result.n_rebalances > 10
    assert result.market_states_used > 0
    assert result.integrity["look_ahead_bias"] == "pass"
    assert result.integrity["risk_firewall"] == "pass"
    assert result.integrity["live_trading_disabled"] == "pass"
    assert result.integrity["transaction_cost_underestimation"] == "pass"
    assert "sharpe" in result.metrics
    assert run.hypothesis_id
    assert run.genome_id
    assert run.lineage["provider"] == "data_fabric"
    assert run.lineage["source"] == "memory_synthetic_nse"
    assert run.data_kind == "synthetic"
    assert run.dataset_id == "synthetic-nse"
    assert run.snapshot_id
    assert result.integrity["survivorship_bias"] == "not_tested"
    assert tmp_ledger.exists()
    assert "cs_momentum_nse_synthetic" in tmp_ledger.read_text(encoding="utf-8")
    assert result.max_drawdown <= 0


@pytest.mark.vertical_slice
def test_slice_is_reproducible(tmp_path: Path) -> None:
    a = run_momentum_vertical_slice(ledger_path=tmp_path / "a.jsonl")
    b = run_momentum_vertical_slice(ledger_path=tmp_path / "b.jsonl")
    assert a[0].total_return == b[0].total_return
    assert a[0].max_drawdown == b[0].max_drawdown
    assert a[0].n_rebalances == b[0].n_rebalances
    assert a[0].metrics["sharpe"] == b[0].metrics["sharpe"]
    assert a[1].id != b[1].id
