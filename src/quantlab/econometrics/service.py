"""Econometric research service. Not a second backtester or FDR engine."""

from __future__ import annotations

from quantlab.core.config import LiveSafetyGates
from quantlab.core.errors import SafetyError
from quantlab.domain.research import IntegrityReport
from quantlab.econometrics.breaks import cusum, rolling_stability
from quantlab.econometrics.causal import did_estimate, hypothesis
from quantlab.econometrics.cointegration import engle_granger, johansen_interface
from quantlab.econometrics.dependence import dependence_report
from quantlab.econometrics.economics import economic_report
from quantlab.econometrics.enums import CausalClaim, EstimatorKind, PanelEffect
from quantlab.econometrics.granger import granger_pair
from quantlab.econometrics.identity import hash_run, hash_spec, idempotency_key
from quantlab.econometrics.inference import hac_slope
from quantlab.econometrics.integrity import EconometricLeakFlags
from quantlab.econometrics.library import (
    cointegrated_pair,
    panel_toy,
    random_walk,
    stationary_ar1,
)
from quantlab.econometrics.models import (
    CausalSpecification,
    EconometricDiagnostics,
    EconometricRequest,
    EconometricResult,
    EconometricRun,
    EconometricSpecification,
)
from quantlab.econometrics.panel import entity_fe, fama_macbeth, panel_spec, pooled_ols
from quantlab.econometrics.state import lookup, put_result
from quantlab.econometrics.stationarity import adf_test, kpss_test, phillips_perron_interface
from quantlab.econometrics.var import fit_var, select_lags
from quantlab.econometrics.vecm import error_correction
from quantlab.research.integrity import evaluate_integrity
from quantlab.research.multiple_testing import evaluate_family


def _integrity(
    flags: EconometricLeakFlags, *, live_trading: bool, data_kind: str
) -> IntegrityReport:
    return evaluate_integrity(
        bars=[],
        states=[],
        as_of_times=[],
        next_bar_fill=True,
        cost_bps=10.0,
        slippage_model="configured",
        live_trading=live_trading,
        n_experiments_in_family=1,
        used_ml=False,
        data_kind=data_kind,
        future_stationarity_window=flags.future_stationarity_window,
        future_lag_selection=flags.future_lag_selection,
        future_break_detection=flags.future_break_detection,
        future_cointegration_selection=flags.future_cointegration_selection,
        future_var_selection=flags.future_var_selection,
        future_causal_control=flags.future_causal_control,
        future_event_window=flags.future_event_window,
        future_parameter_estimation=flags.future_parameter_estimation,
        full_sample_econometric_replay=flags.full_sample_econometric_replay,
        future_residual_normalization=flags.future_residual_normalization,
        future_panel_selection=flags.future_panel_selection,
        causal_post_treatment_control=flags.causal_post_treatment_control,
        lookahead_event_study=flags.lookahead_event_study,
    )


def run_econometrics(request: EconometricRequest | None = None) -> EconometricResult:
    used = request or EconometricRequest()
    if used.live_trading or LiveSafetyGates().live_trading:
        raise SafetyError("LIVE_TRADING must remain false; econometrics does not trade")
    _ = used.future_payload_ignored
    flags = EconometricLeakFlags(
        future_lag_selection=False,
        full_sample_econometric_replay=False,
        future_stationarity_window=False,
        future_parameter_estimation=False,
    )
    _integrity(flags, live_trading=False, data_kind=used.data_kind)
    key = idempotency_key(
        spec_id=used.spec_id,
        as_of=used.as_of.isoformat(),
        seed=used.seed,
        n=used.n,
        version="econo-v1",
    )
    cached = lookup(key)
    if cached is not None:
        return cached
    stationary = stationary_ar1(n=used.n, seed=used.seed)
    walk = random_walk(n=used.n, seed=used.seed + 7)
    y, x = cointegrated_pair(n=used.n, seed=used.seed + 3)
    train_end = max(used.n * 2 // 3, 40)
    spec = EconometricSpecification(
        spec_id=used.spec_id,
        estimator=EstimatorKind.OLS,
        series_ids=("stationary", "walk", "y", "x"),
        lags=1,
        as_of=used.as_of,
        snapshot_id="synthetic-diagnostic",
        seed=used.seed,
    )
    adf_s = adf_test(stationary)
    adf_w = adf_test(walk)
    kpss = kpss_test(stationary)
    _ = phillips_perron_interface(stationary)
    dep = dependence_report(stationary)
    coint = engle_granger(y, x)
    _ = johansen_interface([y, x])
    lag = select_lags([y, x], max_lag=3, train_end=train_end)
    var_spec, _, resid = fit_var([y, x], lags=lag, train_end=train_end)
    vecm_spec, _ = error_correction(y, x, coint.beta or 0.0)
    cause = granger_pair(x, y, lags=lag, seed=used.seed)
    brk = cusum(walk)
    _ = rolling_stability(walk)
    slope, _t = hac_slope(y, x, lags=dep.hac_lags or 1)
    economics = economic_report(statistic=cause.statistic, effect=slope, cost_bps=10.0)
    family = evaluate_family([p for p in [cause.p_value] if p is not None])
    py, px, pent, ptime = panel_toy(n_entity=4, n_time=20, seed=used.seed)
    _ = pooled_ols(py, px)
    _ = entity_fe(py, px, pent)
    _ = fama_macbeth(py, px, ptime)
    panel = panel_spec(PanelEffect.TWO_WAY)
    causal_spec = CausalSpecification(
        hypothesis_id="H-CAUSAL-SEED",
        method=EstimatorKind.DID,
        treatment="treated",
        outcome="y",
        assumptions=("parallel_trends_untested", "no_anticipation"),
        claim=CausalClaim.CAUSAL_UNDER_ASSUMPTIONS,
    )
    treated = [0] * (used.n // 2) + [1] * (used.n - used.n // 2)
    post = [0] * (used.n // 2) + [1] * (used.n - used.n // 2)
    _ = did_estimate(stationary, treated, post, spec=causal_spec)
    _ = hypothesis("DiD seed", "parallel trends untested")
    run = EconometricRun(
        econometrics_run_id=f"ECO-{hash_spec(spec)[:12]}",
        spec_id=spec.spec_id,
        as_of=used.as_of,
        family_id=used.family_id,
        tested_count=family.n_hypotheses,
        live_trading=False,
        note="Synthetic diagnostic. Not NSE evidence. Not a claim.",
    )
    run = run.model_copy(update={"run_hash": hash_run(run)})
    result = EconometricResult(
        run=run,
        spec=spec,
        diagnostics=EconometricDiagnostics(
            stationarity=[adf_s, adf_w, kpss],
            dependence=dep,
            cointegration=coint,
            causality=cause,
            breaks=brk,
            residuals=resid[:, 0].tolist() if resid.ndim == 2 and resid.size else [],
        ),
        var=var_spec,
        vecm=vecm_spec,
        panel=panel,
        causal=causal_spec,
        economics=economics,
        multiple_testing={
            "family_id": used.family_id,
            "method": "" if family.method is None else family.method.value,
            "tested_count": str(family.n_hypotheses),
            "discoveries": str(family.discoveries),
            "note": family.note,
        },
        live_trading=False,
        note=(
            "Synthetic architecture diagnostic. CORRELATION ≠ CAUSATION. "
            "IN-SAMPLE FIT ≠ OOS EVIDENCE. Prompt 05 remains the gate."
        ),
    )
    return put_result(result, key=key)
