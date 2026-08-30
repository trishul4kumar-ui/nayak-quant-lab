"""Filtered HMM is PIT; smoothing and full-sample clustering are blocked for prediction."""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime, timedelta

import pytest

from quantlab.core.errors import RegimeError
from quantlab.core.identifiers import InstrumentId
from quantlab.data.providers.memory import MemoryBarProvider
from quantlab.features.engine import session_calendar
from quantlab.regimes.engine import classify, compute_state_panel
from quantlab.regimes.hmm import _smooth_labels, classify_hmm
from quantlab.regimes.registry import get_regime_model
from quantlab.regimes.snapshot import StateSnapshot


def _append_future(bars: dict[InstrumentId, list], calendar: list[datetime]) -> dict:
    future = deepcopy(bars)
    for inst, series in future.items():
        extra = series[-1].model_copy(deep=True)
        extra.pit.event_time = calendar[-1] + timedelta(days=5)
        extra.pit.effective_time = extra.pit.event_time
        extra.pit.available_time = extra.pit.event_time
        extra.pit.ingestion_time = extra.pit.event_time
        extra.close = extra.close * 1.75
        future[inst] = series + [extra]
    return future


@pytest.mark.regime
def test_future_bars_do_not_change_hmm_filter_at_t() -> None:
    bars = MemoryBarProvider(n_days=50).all_bars()
    calendar = session_calendar(bars)
    as_of = calendar[-8]
    prefix = {
        inst: [b for b in series if b.pit.event_time <= as_of] for inst, series in bars.items()
    }
    model = get_regime_model("hmm_vol_filter")
    before = {row.as_of: row.hard_label for row in classify(model, compute_state_panel(prefix))}
    after = {
        row.as_of: row.hard_label
        for row in classify(model, compute_state_panel(_append_future(bars, calendar)))
    }
    assert before[as_of] == after[as_of]


@pytest.mark.regime
def test_hmm_smoothing_blocked_when_predictive() -> None:
    snaps = compute_state_panel(MemoryBarProvider(n_days=40).all_bars())
    model = get_regime_model("hmm_vol_smooth")
    with pytest.raises(RegimeError, match="smoothed HMM"):
        classify(model, snaps, predictive=True)
    rows = classify(model, snaps, predictive=False)
    assert rows
    assert rows[-1].retrospective is True


@pytest.mark.regime
def test_full_sample_cluster_blocked_when_predictive() -> None:
    snaps = compute_state_panel(MemoryBarProvider(n_days=40).all_bars())
    model = get_regime_model("cluster_vol_full")
    with pytest.raises(RegimeError, match="full-sample clustering"):
        classify(model, snaps, predictive=True)
    rows = classify(model, snaps, predictive=False)
    assert rows[-1].retrospective is True


@pytest.mark.regime
def test_smoothed_labels_can_change_when_future_arrives() -> None:
    short = [1.0 + 0.02 * i for i in range(20)]
    long = short + [40.0] * 20
    labels_short, _ = _smooth_labels(short, 2, 0, 8, 10)
    labels_long, _ = _smooth_labels(long, 2, 0, 8, 10)
    assert labels_short != labels_long[: len(labels_short)]


@pytest.mark.regime
def test_full_sample_cluster_can_change_when_future_arrives() -> None:
    start = datetime(2024, 1, 2, tzinfo=UTC)
    model = get_regime_model("cluster_vol_full")

    def snaps(values: list[float]) -> list[StateSnapshot]:
        return [
            StateSnapshot(as_of=start + timedelta(days=i), realized_vol_20=value, n_names=3)
            for i, value in enumerate(values)
        ]

    short = [1.0] * 12 + [1.2]
    long = short + [20.0] * 12
    a = classify(model, snaps(short), predictive=False)
    b = classify(model, snaps(long), predictive=False)
    assert [row.hard_label for row in a] != [row.hard_label for row in b[: len(a)]]


@pytest.mark.regime
def test_hmm_filter_is_reproducible() -> None:
    snaps = compute_state_panel(MemoryBarProvider(n_days=40).all_bars())
    model = get_regime_model("hmm_vol_filter")
    first = classify_hmm(model, snaps, predictive=True)
    second = classify_hmm(model, snaps, predictive=True)
    assert [row.hard_label for row in first] == [row.hard_label for row in second]
    labelled = [row for row in first if row.hard_label is not None]
    assert labelled
    last = labelled[-1]
    assert last.hard_label in last.probabilities
    assert sum(last.probabilities.values()) == pytest.approx(1.0)
