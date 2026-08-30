"""PIT snapshots, missing values, rule labels, and change-points."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta

import pytest

from quantlab.core.errors import RegimeError
from quantlab.core.identifiers import InstrumentId
from quantlab.data.providers.memory import MemoryBarProvider
from quantlab.features.engine import session_calendar
from quantlab.regimes.engine import classify, compute_state_panel, detect_changes
from quantlab.regimes.normalize import expanding_zscore
from quantlab.regimes.registry import get_regime_model
from quantlab.regimes.snapshot import compute_snapshot


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
def test_future_bars_do_not_change_snapshot_at_t() -> None:
    bars = MemoryBarProvider(n_days=80).all_bars()
    calendar = session_calendar(bars)
    as_of = calendar[-8]
    before = compute_snapshot(bars, as_of)
    after = compute_snapshot(_append_future(bars, calendar), as_of)
    assert before.market_ew_return == after.market_ew_return
    assert before.realized_vol_20 == after.realized_vol_20
    assert before.dispersion_cs == after.dispersion_cs
    assert before.n_names == after.n_names
    assert "nifty" in before.note.lower()


@pytest.mark.regime
def test_future_bars_do_not_change_rule_label_at_t() -> None:
    bars = MemoryBarProvider(n_days=80).all_bars()
    calendar = session_calendar(bars)
    as_of = calendar[-8]
    dates = [d for d in calendar if d <= as_of]
    model = get_regime_model("vol_tercile")
    prefix = {
        inst: [b for b in series if b.pit.event_time <= as_of] for inst, series in bars.items()
    }
    before = {row.as_of: row.hard_label for row in classify(model, compute_state_panel(prefix))}
    after_panel = compute_state_panel(_append_future(bars, calendar))
    after = {row.as_of: row.hard_label for row in classify(model, after_panel)}
    assert before[as_of] == after[as_of]
    assert dates[-1] == as_of


@pytest.mark.regime
def test_future_only_name_is_not_in_snapshot_at_t() -> None:
    bars = MemoryBarProvider(n_days=80).all_bars()
    calendar = session_calendar(bars)
    as_of = calendar[-8]
    before = compute_snapshot(bars, as_of)
    extra_inst = InstrumentId.parse("NSE:FUTUREONLY")
    template = next(iter(bars.values()))[-1].model_copy(deep=True)
    template.instrument = extra_inst
    template.pit.event_time = calendar[-1] + timedelta(days=6)
    template.pit.effective_time = template.pit.event_time
    template.pit.available_time = template.pit.event_time
    template.pit.ingestion_time = template.pit.event_time
    future = deepcopy(bars)
    future[extra_inst] = [template]
    after = compute_snapshot(future, as_of)
    assert before.n_names == after.n_names
    assert before.market_ew_return == after.market_ew_return


@pytest.mark.regime
def test_missing_state_is_none_not_zero() -> None:
    bars = MemoryBarProvider(n_days=80).all_bars()
    calendar = session_calendar(bars)
    snap = compute_snapshot(bars, calendar[-1])
    assert snap.index_nifty_return is None
    assert snap.liquidity_adv is None
    assert 0.0 not in {snap.index_nifty_return, snap.liquidity_adv}
    assert "index_nifty_return" in snap.missing
    assert "liquidity_adv" in snap.missing


@pytest.mark.regime
def test_expanding_zscore_at_t_ignores_future() -> None:
    prefix = [float(i) for i in range(12)]
    full = prefix + [100.0, 200.0]
    z_prefix = expanding_zscore(prefix)
    z_full = expanding_zscore(full)
    assert z_prefix[-1] == z_full[len(prefix) - 1]
    mean = sum(full) / len(full)
    var = sum((x - mean) ** 2 for x in full) / len(full)
    leaked = (prefix[-1] - mean) / (var**0.5)
    assert z_prefix[-1] != pytest.approx(leaked)


@pytest.mark.regime
def test_change_point_is_not_a_regime() -> None:
    bars = MemoryBarProvider(n_days=80).all_bars()
    snaps = compute_state_panel(bars)
    report = detect_changes(snaps)
    assert all(not hasattr(p, "hard_label") for p in report.points)
    assert "not a regime" in report.note.lower()
    with pytest.raises(RegimeError, match="change-point"):
        classify(get_regime_model("cusum_ew"), snaps)


@pytest.mark.regime
def test_hard_label_and_probability_are_separate() -> None:
    bars = MemoryBarProvider(n_days=80).all_bars()
    rows = classify(get_regime_model("vol_tercile"), compute_state_panel(bars))
    labelled = [row for row in rows if row.hard_label is not None]
    assert labelled
    last = labelled[-1]
    assert last.hard_label in last.probabilities
    assert last.probabilities[last.hard_label] == pytest.approx(1.0)
    assert last.retrospective is False
