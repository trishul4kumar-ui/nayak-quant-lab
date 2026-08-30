import pytest

from quantlab.backtest.costs import RESEARCH_COST_GRID_BPS, CostSchedule
from quantlab.backtest.engine import BacktestConfig, run_backtest
from quantlab.backtest.slippage import NoSlippage, VolumeParticipationSlippage
from quantlab.data.providers.memory import MemoryBarProvider
from quantlab.research.momentum import CrossSectionalMomentum
from quantlab.research.robustness import cost_sensitivity, is_fragile, parameter_surface
from quantlab.risk.firewall import RiskFirewall, RiskLimits


def _ready() -> tuple[object, CrossSectionalMomentum, RiskFirewall]:
    provider = MemoryBarProvider(n_days=80)
    firewall = RiskFirewall(RiskLimits(max_name_weight=0.55, max_names=5, max_gross=1.05))
    firewall.register_instruments(provider.get_instruments())
    return provider.all_bars(), CrossSectionalMomentum(lookback=20, top_n=2), firewall


def test_cost_grid_is_non_negative_and_excludes_zero() -> None:
    assert 0.0 not in RESEARCH_COST_GRID_BPS
    bars, strategy, firewall = _ready()
    points = cost_sensitivity(bars, strategy, firewall, 20)
    assert [p.cost_bps for p in points] == list(RESEARCH_COST_GRID_BPS)
    assert all(p.cost_bps > 0 for p in points)


def test_cost_schedule_unspecified_taxes_stay_zero() -> None:
    schedule = CostSchedule()
    assert schedule.commission_bps == 10.0
    assert schedule.stt_bps == 0.0
    assert "unspecified" in schedule.provenance


def test_volume_participation_unevaluable() -> None:
    assert VolumeParticipationSlippage().extra_bps() is None
    assert NoSlippage().extra_bps() == 0.0


def test_parameter_surface_and_fragility() -> None:
    bars, _, firewall = _ready()
    points = parameter_surface(bars, firewall, (10, 15, 20), top_n=2, cost_bps=10.0)
    assert len(points) == 3
    assert is_fragile(points) in {True, False}


def test_same_bar_fill_rejected() -> None:
    with pytest.raises(ValueError, match="next_bar"):
        BacktestConfig(fill_policy="same_bar")


def test_eval_window_is_subset() -> None:
    bars, strategy, firewall = _ready()
    full = run_backtest(bars, strategy, firewall, BacktestConfig(lookback=20, cost_bps=10.0))
    mid = full.dates[len(full.dates) // 2]
    windowed = run_backtest(
        bars,
        strategy,
        firewall,
        BacktestConfig(lookback=20, cost_bps=10.0, eval_start=mid),
    )
    assert windowed.n_rebalances < full.n_rebalances
    assert windowed.dates[0] >= mid
