from datetime import timedelta
from pathlib import Path

from quantlab.backtest.engine import BacktestConfig, run_backtest
from quantlab.data.providers.memory import MemoryBarProvider
from quantlab.research.momentum import CrossSectionalMomentum
from quantlab.risk.firewall import RiskFirewall, RiskLimits
from tests.data.helpers import make_bar


def test_backtest_cannot_see_delayed_restatement() -> None:
    provider = MemoryBarProvider(n_days=60)
    instruments = provider.get_instruments()
    bars = provider.all_bars()
    strategy = CrossSectionalMomentum(lookback=20, top_n=2)
    firewall = RiskFirewall(RiskLimits(max_name_weight=0.55, max_names=5, max_gross=1.05))
    firewall.register_instruments(instruments)
    clean = run_backtest(bars, strategy, firewall, BacktestConfig(lookback=20, cost_bps=10.0))

    victim = instruments[0].id
    series = bars[victim]
    mid = series[30]
    leaked = make_bar(
        victim.symbol,
        mid.pit.event_time,
        close=mid.close * 50.0,
        available=mid.pit.available_time + timedelta(days=20),
    )
    bars[victim] = [*series, leaked]
    dirty = run_backtest(bars, strategy, firewall, BacktestConfig(lookback=20, cost_bps=10.0))
    assert clean.total_return == dirty.total_return
    assert clean.n_rebalances == dirty.n_rebalances


def test_fabric_slice_records_dataset_provenance(tmp_path: Path) -> None:
    from quantlab.research.pipeline import run_momentum_vertical_slice

    result, run = run_momentum_vertical_slice(
        ledger_path=tmp_path / "ledger.jsonl",
        fabric_root=tmp_path / "fabric",
        n_days=50,
    )
    assert result.n_rebalances > 5
    assert run.dataset_id == "synthetic-nse"
    assert run.data_kind == "synthetic"
    assert run.lineage["provider"] == "data_fabric"
    assert run.integrity["corporate_action_leakage"] == "not_tested"
    assert run.integrity["survivorship_bias"] == "not_tested"
