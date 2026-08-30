from quantlab.alpha.decay import predictive_decay
from quantlab.alpha.experiment import (
    AlphaExperimentConfig,
    panels_almost_equal,
    run_feature_experiment,
)
from quantlab.alpha.synthetics import (
    leaky_forward_panel,
    null_independent_bars,
    planted_volume_predicts_return,
)
from quantlab.core.identifiers import InstrumentId
from quantlab.domain.models import Instrument
from quantlab.domain.research import CheckResult
from quantlab.features.engine import compute_panel, session_calendar
from quantlab.features.registry import get_feature
from quantlab.labels.definition import forward_return
from quantlab.labels.engine import compute_label_panel
from quantlab.research.gate import GateOutcome


def _instruments(bars: dict[InstrumentId, list[object]]) -> list[Instrument]:
    return [Instrument(id=inst, name=inst.symbol) for inst in bars]


def test_planted_volume_signal_is_detected() -> None:
    bars = planted_volume_predicts_return()
    feature = get_feature("rank_volume")
    label = forward_return(1)
    report, run = run_feature_experiment(
        bars=bars,
        instruments=_instruments(bars),
        feature=feature,
        label=label,
        config=AlphaExperimentConfig(
            feature_id="rank_volume",
            n_hypotheses_in_family=3,
            family_id="planted_volume",
            data_kind="synthetic",
        ),
        append=False,
    )
    assert report.ic.spearman_mean is not None
    assert report.ic.spearman_mean > 0.5
    assert run.n_hypotheses_in_family == 3
    assert report.gate.outcome is GateOutcome.WARN
    assert report.gate.outcome is not GateOutcome.RESEARCH_CANDIDATE
    assert report.integrity["label_as_feature"] == "pass"
    assert report.integrity["synthetic_data"] == "warn"


def test_null_feature_is_not_strong_alpha() -> None:
    bars = null_independent_bars()
    report, _ = run_feature_experiment(
        bars=bars,
        instruments=_instruments(bars),
        feature=get_feature("rank_volume"),
        label=forward_return(1),
        config=AlphaExperimentConfig(feature_id="rank_volume", data_kind="synthetic"),
        append=False,
    )
    assert report.ic.spearman_mean is None or abs(report.ic.spearman_mean) < 0.45


def test_decay_stronger_at_short_horizon() -> None:
    bars = planted_volume_predicts_return(n_sessions=60)
    dates = session_calendar(bars)
    feature = compute_panel(get_feature("rank_volume"), bars, dates)
    decay = predictive_decay(feature, bars, horizons=(1, 5, 20), min_sample=8)
    short = next(p for p in decay.points if p.horizon == 1)
    long = next(p for p in decay.points if p.horizon == 20)
    assert short.spearman_mean is not None
    assert long.spearman_mean is not None
    assert short.spearman_mean >= long.spearman_mean - 0.05


def test_leaky_future_label_fails_integrity() -> None:
    bars = planted_volume_predicts_return()
    dates = session_calendar(bars)
    labels = compute_label_panel(forward_return(1), bars, dates)
    leaky = leaky_forward_panel(labels)
    assert panels_almost_equal(leaky, labels)
    report, _ = run_feature_experiment(
        bars=bars,
        instruments=_instruments(bars),
        feature=get_feature("rank_volume"),
        label=forward_return(1),
        config=AlphaExperimentConfig(feature_id="rank_volume", data_kind="synthetic"),
        append=False,
    )
    # Engine rank_volume is not the label; explicit leak flag is tested via panels_almost_equal.
    assert report.integrity["label_as_feature"] == "pass"
    from quantlab.research.integrity import evaluate_integrity

    leaked = evaluate_integrity(
        bars=[bar for series in bars.values() for bar in series],
        states=[],
        as_of_times=dates,
        next_bar_fill=True,
        cost_bps=10.0,
        slippage_model="none",
        live_trading=False,
        n_experiments_in_family=1,
        used_ml=False,
        label_used_as_feature=True,
        future_normalization=True,
        future_ranking_universe=True,
    )
    assert leaked.checks["label_as_feature"] is CheckResult.FAIL
    assert leaked.checks["future_normalization"] is CheckResult.FAIL
    assert leaked.checks["future_ranking_universe"] is CheckResult.FAIL
    assert leaked.failed()


def test_constant_feature_is_not_tested_ic() -> None:
    from datetime import UTC, datetime

    from quantlab.alpha.ic import information_coefficient

    day = datetime(2024, 1, 2, tzinfo=UTC)
    feature = {day: {"NSE:A": 1.0, "NSE:B": 1.0, "NSE:C": 1.0}}
    label = {day: {"NSE:A": 0.1, "NSE:B": 0.2, "NSE:C": -0.1}}
    report = information_coefficient(feature, label, min_sample=8)
    assert report.status is CheckResult.NOT_TESTED
