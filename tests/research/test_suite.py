from pathlib import Path

import pytest

from quantlab.backtest.engine import BacktestConfig, run_backtest
from quantlab.core.identifiers import InstrumentId
from quantlab.data.providers.memory import MemoryBarProvider
from quantlab.domain.models import Instrument, OHLCVBar
from quantlab.domain.research import CheckResult
from quantlab.math.metrics import max_drawdown
from quantlab.research.baselines import RandomSignalBaseline
from quantlab.research.gate import GateOutcome
from quantlab.research.momentum import CrossSectionalMomentum
from quantlab.research.pipeline import run_momentum_validation
from quantlab.research.suite import ValidationConfig, run_validation_suite
from quantlab.risk.firewall import RiskFirewall, RiskLimits


def _loaded() -> tuple[dict[InstrumentId, list[OHLCVBar]], list[Instrument]]:
    provider = MemoryBarProvider(n_days=80)
    return provider.all_bars(), provider.get_instruments()


def test_validation_properties_and_synthetic_gate() -> None:
    bars, instruments = _loaded()
    result, report = run_validation_suite(
        bars,
        instruments,
        config=ValidationConfig(lookback=20, top_n=2, cost_bps=10.0, n_boot=40, n_perm=40),
        data_kind="synthetic",
        dataset_id="synthetic-nse",
        dataset_version="v1",
        snapshot_id="snap",
    )
    assert result.max_drawdown <= 0
    assert result.ending_equity >= 0
    assert result.cost_drag >= 0
    assert report.oos_windows >= 1
    assert report.walk_forward.windows_temporally_ok
    assert report.gate.outcome is GateOutcome.WARN
    assert report.gate.outcome is not GateOutcome.PROMOTED_TO_PAPER
    assert report.attribution.status is CheckResult.NOT_TESTED
    assert report.liquidity.status is CheckResult.NOT_TESTED
    assert report.overfitting.status is CheckResult.NOT_TESTED
    for window in report.walk_forward.plan.windows:
        assert window.train_end < window.test_start


def test_random_baseline_is_seeded() -> None:
    bars, instruments = _loaded()
    firewall = RiskFirewall(RiskLimits(max_name_weight=0.55, max_names=5, max_gross=1.05))
    firewall.register_instruments(instruments)
    a = run_backtest(
        bars,
        RandomSignalBaseline(seed=7, top_n=2),
        firewall,
        BacktestConfig(lookback=20, cost_bps=10.0, seed=7),
    )
    b = run_backtest(
        bars,
        RandomSignalBaseline(seed=7, top_n=2),
        firewall,
        BacktestConfig(lookback=20, cost_bps=10.0, seed=7),
    )
    assert a.total_return == b.total_return


def test_empty_universe_non_negative() -> None:
    firewall = RiskFirewall()
    firewall.register_instruments([])
    result = run_backtest(
        {},
        CrossSectionalMomentum(lookback=5, top_n=1),
        firewall,
        BacktestConfig(lookback=5, cost_bps=10.0),
    )
    assert result.ending_equity >= 0
    assert max_drawdown(result.equity_curve) <= 0


@pytest.mark.validation
def test_pipeline_validation_writes_artifacts(tmp_path: Path) -> None:
    result, run, report = run_momentum_validation(
        ledger_path=tmp_path / "ledger.jsonl",
        fabric_root=tmp_path / "fabric",
        artifacts_dir=tmp_path / "artifacts",
        config=ValidationConfig(lookback=20, top_n=2, cost_bps=10.0, n_boot=30, n_perm=30),
    )
    assert run.data_kind == "synthetic"
    assert run.gate_outcome == GateOutcome.WARN.value
    assert (tmp_path / "artifacts" / run.id / "validation.json").exists()
    assert run.n_hypotheses_in_family == 5
    assert result.integrity["look_ahead_bias"] == "pass"
    assert result.integrity["transaction_cost_underestimation"] == "pass"
    assert report.performance.risk_free_convention
