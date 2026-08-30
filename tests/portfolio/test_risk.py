"""PIT covariance, min-variance closed form, and look-ahead invariance."""

from __future__ import annotations

from copy import deepcopy
from datetime import timedelta

import numpy as np
import pytest

from quantlab.core.errors import OptimizationError
from quantlab.data.providers.memory import MemoryBarProvider
from quantlab.portfolio.builder import construct_targets
from quantlab.portfolio.constraints import long_only_invested
from quantlab.portfolio.covariance import as_array, sample_covariance
from quantlab.portfolio.optimize import (
    equal_risk_contribution,
    min_variance_closed_form,
    min_variance_long_only,
)
from quantlab.portfolio.spec import ConstructorKind, PortfolioModel


@pytest.mark.portfolio
def test_two_asset_min_variance_analytic() -> None:
    cov = np.array([[0.04, 0.0], [0.0, 0.01]], dtype=np.float64)
    closed = min_variance_closed_form(cov)
    projected = min_variance_long_only(cov)
    expected = np.array([0.2, 0.8])
    assert closed == pytest.approx(expected, abs=1e-8)
    assert projected == pytest.approx(expected, abs=1e-6)


@pytest.mark.portfolio
def test_erc_equal_vol_is_equal_weight() -> None:
    weights = equal_risk_contribution(np.eye(3, dtype=np.float64))
    assert weights == pytest.approx(np.full(3, 1.0 / 3.0), abs=1e-6)


@pytest.mark.portfolio
def test_erc_rejects_shorts() -> None:
    model = PortfolioModel(
        portfolio_id="erc",
        version="1",
        name="erc",
        ensemble_id="mom20",
        constructor=ConstructorKind.RISK_PARITY,
        long_only=False,
        constraints=[],
        covariance_lookback=20,
    )
    bars = MemoryBarProvider(n_days=80).all_bars()
    as_of = sorted({b.pit.event_time for series in bars.values() for b in series})[-1]
    scores = {str(inst): 1.0 for inst in bars}
    with pytest.raises(OptimizationError, match="long-only"):
        construct_targets(model, scores, as_of, bars=bars)


@pytest.mark.portfolio
def test_covariance_is_symmetric_psd_and_pit() -> None:
    provider = MemoryBarProvider(n_days=80)
    bars = provider.all_bars()
    names = [str(inst) for inst in bars]
    calendar = sorted({b.pit.event_time for series in bars.values() for b in series})
    as_of = calendar[-5]
    report = sample_covariance(bars, as_of, names, lookback=20)
    matrix = as_array(report)
    assert np.allclose(matrix, matrix.T)
    assert report.psd
    assert report.min_eigenvalue is not None and report.min_eigenvalue >= -1e-10
    future = deepcopy(bars)
    for inst, series in future.items():
        extra = series[-1].model_copy(deep=True)
        extra.pit.event_time = calendar[-1] + timedelta(days=3)
        extra.pit.effective_time = extra.pit.event_time
        extra.pit.available_time = extra.pit.event_time
        extra.pit.ingestion_time = extra.pit.event_time
        extra.close = extra.close * 1.5
        future[inst] = series + [extra]
    later = sample_covariance(future, as_of, names, lookback=20)
    assert as_array(report) == pytest.approx(as_array(later), abs=1e-12)


@pytest.mark.portfolio
def test_future_bars_do_not_change_weights_at_t() -> None:
    provider = MemoryBarProvider(n_days=80)
    bars = provider.all_bars()
    calendar = sorted({b.pit.event_time for series in bars.values() for b in series})
    as_of = calendar[-8]
    scores = {str(inst): float(i + 1) for i, inst in enumerate(sorted(bars, key=str))}
    model = PortfolioModel(
        portfolio_id="mv",
        version="1",
        name="mv",
        ensemble_id="mom20",
        constructor=ConstructorKind.MIN_VARIANCE,
        constraints=long_only_invested(),
        covariance_lookback=20,
    )
    proposal, _, _ = construct_targets(model, scores, as_of, bars=bars)
    future = deepcopy(bars)
    for inst, series in future.items():
        extra = series[-1].model_copy(deep=True)
        extra.pit.event_time = calendar[-1] + timedelta(days=4)
        extra.pit.effective_time = extra.pit.event_time
        extra.pit.available_time = extra.pit.event_time
        extra.pit.ingestion_time = extra.pit.event_time
        extra.close *= 2.0
        future[inst] = series + [extra]
    later, _, _ = construct_targets(model, scores, as_of, bars=future)
    left = {str(t.instrument): t.weight for t in proposal.targets}
    right = {str(t.instrument): t.weight for t in later.targets}
    assert left.keys() == right.keys()
    for key in left:
        assert left[key] == pytest.approx(right[key], abs=1e-12)
