"""Stability, residuals, importance, incremental IC. Importance is not causality."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from quantlab.adaptive.decay import estimate_half_life
from quantlab.adaptive.state import DecayEstimate
from quantlab.domain.research import CheckResult
from quantlab.features.engine import Panel
from quantlab.learning.dataset import ModelDataset, row_xy
from quantlab.learning.estimators import predict_model
from quantlab.learning.state import ModelState
from quantlab.research.cross_section import spearman_ic


class ResidualReport(BaseModel):
    mean: float | None = None
    variance: float | None = None
    lag1_autocorr: float | None = None
    n: int = 0
    status: CheckResult = CheckResult.NOT_TESTED
    note: str = "Diagnostics do not prove residual assumptions."


class ImportanceReport(BaseModel):
    method: str
    scores: dict[str, float] = Field(default_factory=dict)
    note: str = "Feature importance is a diagnostic, not causal importance."


class StabilityReport(BaseModel):
    n_sign_changes: int = 0
    coefficient_dispersion: float | None = None
    flags: list[str] = Field(default_factory=list)
    status: CheckResult = CheckResult.NOT_TESTED
    note: str = "Stability of fitted structure, not of markets."


class IncrementalReport(BaseModel):
    baseline_ic: float | None = None
    candidate_ic: float | None = None
    delta_ic: float | None = None
    n: int = 0
    note: str = "Incremental information, not standalone strength."


def residual_report(predicted: list[float], actual: list[float]) -> ResidualReport:
    if len(predicted) != len(actual) or len(predicted) < 3:
        return ResidualReport(n=len(predicted), status=CheckResult.NOT_TESTED)
    resid = [actual[i] - predicted[i] for i in range(len(actual))]
    n = len(resid)
    mean = sum(resid) / n
    var = sum((v - mean) ** 2 for v in resid) / n
    lag = None
    if n >= 4:
        a = resid[:-1]
        b = resid[1:]
        ma = sum(a) / len(a)
        mb = sum(b) / len(b)
        num = sum((a[i] - ma) * (b[i] - mb) for i in range(len(a)))
        da = sum((v - ma) ** 2 for v in a)
        db = sum((v - mb) ** 2 for v in b)
        if da > 0 and db > 0:
            lag = num / (da**0.5 * db**0.5)
    return ResidualReport(
        mean=mean,
        variance=var,
        lag1_autocorr=lag,
        n=n,
        status=CheckResult.PASS,
    )


def linear_importance(state: ModelState) -> ImportanceReport:
    artifact = state.artifact
    if artifact is None or not artifact.coefficients:
        return ImportanceReport(method="none", note="no linear coefficients")
    names = artifact.selected or artifact.feature_names
    scores = {
        names[i]: abs(artifact.coefficients[i])
        for i in range(min(len(names), len(artifact.coefficients)))
    }
    return ImportanceReport(method="abs_coefficient", scores=scores)


def permutation_importance(
    state: ModelState,
    dataset: ModelDataset,
    dates: list[datetime],
    seed: int = 0,
) -> ImportanceReport:
    artifact = state.artifact
    if artifact is None:
        return ImportanceReport(method="permutation")
    names = artifact.feature_names or dataset.feature_ids
    base = _panel_ic(state, dataset, dates, None, seed)
    scores: dict[str, float] = {}
    for j, name in enumerate(names):
        perm = _panel_ic(state, dataset, dates, j, seed)
        if base is not None and perm is not None:
            scores[name] = base - perm
    return ImportanceReport(method="permutation_ic_drop", scores=scores)


def coefficient_stability(states: list[ModelState]) -> StabilityReport:
    series = [s.artifact.coefficients for s in states if s.artifact and s.artifact.coefficients]
    if len(series) < 3:
        return StabilityReport(flags=["insufficient_history"], status=CheckResult.NOT_TESTED)
    p = len(series[0])
    flips = 0
    disp = 0.0
    for j in range(p):
        col = [row[j] for row in series if len(row) > j]
        for i in range(1, len(col)):
            if col[i] * col[i - 1] < 0:
                flips += 1
        mu = sum(col) / len(col)
        disp += sum((v - mu) ** 2 for v in col) / len(col)
    flags = []
    if flips > len(series):
        flags.append("unstable_signs")
    return StabilityReport(
        n_sign_changes=flips,
        coefficient_dispersion=disp / max(p, 1),
        flags=flags,
        status=CheckResult.WARN if flags else CheckResult.PASS,
    )


def incremental_ic(baseline: Panel, candidate: Panel, labels: Panel) -> IncrementalReport:
    bics: list[float] = []
    cics: list[float] = []
    for as_of, lab in labels.items():
        b = spearman_ic(baseline.get(as_of, {}), lab)
        c = spearman_ic(candidate.get(as_of, {}), lab)
        if b is not None:
            bics.append(b)
        if c is not None:
            cics.append(c)
    bmean = None if not bics else sum(bics) / len(bics)
    cmean = None if not cics else sum(cics) / len(cics)
    delta = None if bmean is None or cmean is None else cmean - bmean
    return IncrementalReport(
        baseline_ic=bmean,
        candidate_ic=cmean,
        delta_ic=delta,
        n=min(len(bics), len(cics)),
    )


def model_decay(ics: list[float]) -> DecayEstimate:
    return estimate_half_life(ics)


def _panel_ic(
    state: ModelState,
    dataset: ModelDataset,
    dates: list[datetime],
    permute_j: int | None,
    seed: int,
) -> float | None:
    ics: list[float] = []
    rng = [seed]
    for as_of in dates:
        insts, xs, _ys = row_xy(dataset, as_of, state.feature_schema)
        if not insts:
            continue
        if permute_j is not None:
            col = [row[permute_j] for row in xs]
            for i in range(len(col) - 1, 0, -1):
                rng[0] = (1103515245 * rng[0] + 12345) % (2**31)
                j = rng[0] % (i + 1)
                col[i], col[j] = col[j], col[i]
            xs = [list(row) for row in xs]
            for i, row in enumerate(xs):
                row[permute_j] = col[i]
        try:
            pred = predict_model(state, xs)
        except Exception:
            continue
        scores = dict(zip(insts, pred, strict=True))
        ic = spearman_ic(scores, dataset.labels.get(as_of, {}))
        if ic is not None:
            ics.append(ic)
    if not ics:
        return None
    return sum(ics) / len(ics)
