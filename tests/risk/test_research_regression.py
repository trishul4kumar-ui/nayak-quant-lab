"""OLS intercept is a model estimate. Decomposition missing B stays NOT_TESTED."""

from __future__ import annotations

from datetime import UTC, datetime

import numpy as np
import pytest

from quantlab.data.providers.memory import MemoryBarProvider
from quantlab.domain.research import CheckResult
from quantlab.factors.exposure import ExposureMatrix
from quantlab.features.engine import session_calendar
from quantlab.portfolio.baselines import equal_weight_names, targets_to_map
from quantlab.portfolio.covariance import CovarianceReport, estimate_covariance
from quantlab.risk.decomposition import decompose_portfolio_variance
from quantlab.risk.regression import ols


@pytest.mark.factor
def test_regression_intercept_is_labeled() -> None:
    y = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    report = ols(y, {"f": [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]})
    assert report.intercept_label == "model intercept estimate"
    assert "model estimate" in report.note
    assert report.n == 6


@pytest.mark.factor
def test_high_condition_number_warns() -> None:
    y = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
    col_a = [float(i) for i in range(8)]
    col_b = [float(i) + 0.01 for i in range(8)]
    report = ols(y, {"a": col_a, "b": col_b})
    assert len(report.vif) == 2
    assert max(report.vif) > 5


@pytest.mark.factor
def test_decomposition_without_b_is_not_tested() -> None:
    bars = MemoryBarProvider(n_days=80).all_bars()
    names = [str(inst) for inst in bars]
    calendar = session_calendar(bars)
    cov = estimate_covariance(bars, calendar[-1], names, 20)
    weights = targets_to_map(equal_weight_names({n: 1.0 for n in cov.names}))
    report = decompose_portfolio_variance(weights, cov)
    assert report.status is CheckResult.NOT_TESTED
    assert report.total_variance is not None
    assert report.factor_variance is None


@pytest.mark.factor
def test_decomposition_with_b_splits_variance() -> None:
    as_of = datetime(2024, 1, 2, tzinfo=UTC)
    sigma = np.array([[0.04, 0.01], [0.01, 0.04]], dtype=np.float64)
    cov = CovarianceReport(
        names=["NSE:A", "NSE:B"],
        matrix=sigma.tolist(),
        lookback=20,
        estimator="sample",
        as_of=as_of,
        n_obs=20,
        psd=True,
        status=CheckResult.PASS,
    )
    exposures = ExposureMatrix(
        as_of=as_of,
        names=["NSE:A", "NSE:B"],
        factor_ids=["market_ew_beta"],
        matrix=[[1.0], [1.0]],
    )
    omega = np.array([[0.02]], dtype=np.float64)
    weights = {"NSE:A": 0.5, "NSE:B": 0.5}
    report = decompose_portfolio_variance(weights, cov, exposures, omega)
    assert report.status is CheckResult.PASS
    assert report.factor_variance is not None
    assert report.idiosyncratic_variance is not None
    assert report.factor_share is not None
    assert report.factor_variance >= -1e-12
    assert report.idiosyncratic_variance >= -1e-12
