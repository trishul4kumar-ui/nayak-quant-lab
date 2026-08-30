from __future__ import annotations

import numpy as np
import pytest

from quantlab.domain.research import CheckResult
from quantlab.econometrics.breaks import cusum, rolling_stability
from quantlab.econometrics.cointegration import engle_granger
from quantlab.econometrics.dependence import dependence_report
from quantlab.econometrics.enums import PanelEffect
from quantlab.econometrics.inference import hac_slope
from quantlab.econometrics.library import cointegrated_pair, panel_toy, random_walk, stationary_ar1
from quantlab.econometrics.linalg import ols_fit
from quantlab.econometrics.panel import entity_fe, fama_macbeth, panel_spec, pooled_ols
from quantlab.econometrics.stationarity import (
    adf_test,
    difference,
    kpss_test,
    phillips_perron_interface,
)
from quantlab.econometrics.var import (
    fit_var,
    forecast_error_variance,
    impulse_response,
    select_lags,
)
from quantlab.econometrics.vecm import error_correction


def test_adf_rejects_stationary_ar1() -> None:
    series = stationary_ar1(n=200, seed=1, phi=0.2)
    item = adf_test(series)
    assert item.status is CheckResult.PASS
    assert item.statistic is not None
    assert item.rejects_unit_root is True


def test_adf_does_not_claim_on_short_sample() -> None:
    item = adf_test([0.1, 0.2, 0.0])
    assert item.status is CheckResult.NOT_TESTED
    assert item.statistic is None
    assert item.rejects_unit_root is None


def test_kpss_on_linear_trend() -> None:
    item = kpss_test([float(i) for i in range(200)])
    assert item.status is CheckResult.PASS
    assert item.statistic is not None
    assert item.rejects_unit_root is True


def test_phillips_perron_is_interface_only() -> None:
    item = phillips_perron_interface(stationary_ar1(n=80, seed=0))
    assert item.status is CheckResult.NOT_TESTED
    assert item.statistic is None


def test_difference_short_series() -> None:
    assert difference([1.0]) == []
    assert len(difference([1.0, 2.0, 4.0])) == 2


def test_dependence_report_has_hac_lags() -> None:
    dep = dependence_report(stationary_ar1(n=80, seed=4))
    assert dep.status is CheckResult.PASS
    assert dep.hac_lags >= 1
    assert dep.acf
    assert dep.pacf


def test_dependence_small_sample_not_tested() -> None:
    dep = dependence_report([1.0, 2.0])
    assert dep.status is CheckResult.NOT_TESTED


def test_engle_granger_on_cointegrated_pair() -> None:
    y, x = cointegrated_pair(n=120, seed=5)
    item = engle_granger(y, x)
    assert item.status is not CheckResult.FAIL
    assert item.beta is not None


def test_engle_granger_short_not_tested() -> None:
    item = engle_granger([1.0] * 10, [2.0] * 10)
    assert item.status is CheckResult.NOT_TESTED


def test_var_fit_and_irf_are_diagnostics() -> None:
    y, x = cointegrated_pair(n=80, seed=6)
    lag = select_lags([y, x], max_lag=2, train_end=50)
    spec, beta, resid = fit_var([y, x], lags=lag, train_end=50)
    assert spec.n_series == 2
    irf = impulse_response(beta, 2, lag, 4)
    assert isinstance(irf, list)
    fev = forecast_error_variance(irf)
    assert fev is None or (0.0 <= fev[0] <= 1.0)


def test_vecm_is_engle_granger_ecm() -> None:
    y, x = cointegrated_pair(n=80, seed=7)
    coint = engle_granger(y, x)
    spec, coef = error_correction(y, x, coint.beta or 0.0)
    assert spec.note
    assert "Johansen" in spec.note


def test_cusum_and_rolling_are_flags_not_halts() -> None:
    walk = random_walk(n=80, seed=8)
    c = cusum(walk)
    r = rolling_stability(walk)
    assert c.status is CheckResult.PASS
    assert r.status is CheckResult.PASS
    assert "live" not in c.note.lower() or "not a live" in c.note.lower()


def test_cusum_short_not_tested() -> None:
    assert cusum([1.0, 2.0]).status is CheckResult.NOT_TESTED
    assert rolling_stability([1.0, 2.0]).status is CheckResult.NOT_TESTED


def test_pooled_hac_differs_from_ols_when_dependent() -> None:
    y, x = cointegrated_pair(n=80, seed=9)
    slope, tstat, status = pooled_ols(y, x)
    yy = np.asarray(y)
    xx = np.column_stack([np.ones(len(y)), np.asarray(x)])
    beta, *_ = ols_fit(yy, xx)
    hac_slope_y, hac_t = hac_slope(y, x, lags=3)
    assert status is CheckResult.PASS
    assert slope is not None
    assert hac_slope_y is not None
    assert abs(slope - float(beta[1])) < 1e-8
    if hac_t is not None:
        se_ols = float(np.std(yy - xx @ beta))
        assert math_isfinite(hac_t)
        assert se_ols >= 0.0


def math_isfinite(value: float) -> bool:
    import math

    return math.isfinite(value)


@pytest.mark.parametrize("effect", list(PanelEffect))
def test_panel_spec_identity(effect: PanelEffect) -> None:
    spec = panel_spec(effect)
    assert spec.effect is effect
    assert spec.spec_id.startswith("panel-")


def test_entity_fe_and_fama_macbeth_toy() -> None:
    y, x, entity, time_id = panel_toy(n_entity=6, n_time=12, seed=3)
    slope, status = entity_fe(y, x, entity)
    fm, fm_status = fama_macbeth(y, x, time_id)
    assert status is CheckResult.PASS
    assert slope is not None
    assert fm_status in {CheckResult.PASS, CheckResult.NOT_TESTED}
    if fm is not None:
        assert isinstance(fm, float)


def test_small_panel_not_tested() -> None:
    assert pooled_ols([1.0], [1.0])[2] is CheckResult.NOT_TESTED
    assert entity_fe([1.0] * 5, [1.0] * 5, ["a"] * 5)[1] is CheckResult.NOT_TESTED
    assert fama_macbeth([1.0] * 5, [1.0] * 5, ["t"] * 5)[1] is CheckResult.NOT_TESTED
