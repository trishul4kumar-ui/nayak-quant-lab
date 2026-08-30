"""1-D Gaussian HMM. Filtered ≠ smoothed. Smoothing is retrospective."""

from __future__ import annotations

import math

import numpy as np

from quantlab.core.errors import RegimeError
from quantlab.domain.research import CheckResult
from quantlab.regimes.definition import RegimeModel
from quantlab.regimes.detectors import RegimeObservation
from quantlab.regimes.normalize import series_of
from quantlab.regimes.snapshot import StateSnapshot


def classify_hmm(
    model: RegimeModel,
    snapshots: list[StateSnapshot],
    *,
    predictive: bool = True,
) -> list[RegimeObservation]:
    field = model.state_features[0] if model.state_features else "realized_vol_20"
    raw = [v for v in series_of(snapshots, field)]
    y = _finite_series(raw)
    n_states = int(model.parameters.get("n_states", 2))
    seed = int(model.parameters.get("seed", 0))
    n_iter = int(model.parameters.get("n_iter", 8))
    min_obs = model.min_obs
    if model.detector.value == "hmm_smooth":
        if predictive:
            raise RegimeError(
                "smoothed HMM uses the full sample and is not a predictive or backtest feature"
            )
        labels, probs = _smooth_labels(y, n_states, seed, n_iter, min_obs)
        return _observations(snapshots, raw, labels, probs, "hmm_smooth", retrospective=True)
    labels, probs = _filter_labels(y, n_states, seed, n_iter, min_obs)
    return _observations(snapshots, raw, labels, probs, "hmm_filter", retrospective=False)


def _finite_series(raw: list[float | None]) -> list[float]:
    return [v for v in raw if v is not None]


def _filter_labels(
    y: list[float],
    n_states: int,
    seed: int,
    n_iter: int,
    min_obs: int,
) -> tuple[list[int | None], list[dict[str, float]]]:
    labels: list[int | None] = []
    probs: list[dict[str, float]] = []
    for t in range(len(y)):
        prefix = np.asarray(y[: t + 1], dtype=np.float64)
        if len(prefix) < min_obs:
            labels.append(None)
            probs.append({})
            continue
        means, vars_, start, trans = _em(prefix, n_states, seed, n_iter)
        path = _viterbi(prefix, means, vars_, start, trans)
        post = _forward_posterior(prefix, means, vars_, start, trans)
        labels.append(int(path[-1]))
        probs.append({f"state_{k}": float(post[-1, k]) for k in range(n_states)})
    return labels, probs


def _smooth_labels(
    y: list[float],
    n_states: int,
    seed: int,
    n_iter: int,
    min_obs: int,
) -> tuple[list[int | None], list[dict[str, float]]]:
    if len(y) < min_obs:
        return [None] * len(y), [{} for _ in y]
    arr = np.asarray(y, dtype=np.float64)
    means, vars_, start, trans = _em(arr, n_states, seed, n_iter)
    gamma = _forward_backward(arr, means, vars_, start, trans)
    labels: list[int | None] = [int(np.argmax(gamma[t])) for t in range(len(y))]
    probs = [{f"state_{k}": float(gamma[t, k]) for k in range(n_states)} for t in range(len(y))]
    return labels, probs


def _observations(
    snapshots: list[StateSnapshot],
    raw: list[float | None],
    compact_labels: list[int | None],
    compact_probs: list[dict[str, float]],
    method: str,
    *,
    retrospective: bool,
) -> list[RegimeObservation]:
    rows: list[RegimeObservation] = []
    j = 0
    for snap, value in zip(snapshots, raw, strict=True):
        if value is None:
            rows.append(
                RegimeObservation(
                    as_of=snap.as_of,
                    method=method,
                    retrospective=retrospective,
                    status=CheckResult.NOT_TESTED,
                    note="missing state variable",
                )
            )
            continue
        label = compact_labels[j]
        probs = compact_probs[j]
        j += 1
        hard = None if label is None else f"state_{label}"
        conf = None if not probs else max(probs.values())
        rows.append(
            RegimeObservation(
                as_of=snap.as_of,
                hard_label=hard,
                probabilities=probs,
                confidence=conf,
                method=method,
                retrospective=retrospective,
                status=CheckResult.NOT_TESTED if hard is None else CheckResult.PASS,
                note=(
                    "retrospective smoothed inference; not a trading feature"
                    if retrospective
                    else "filtered inference using observations through T"
                ),
            )
        )
    return rows


def _em(
    y: np.ndarray,
    n_states: int,
    seed: int,
    n_iter: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    qs = np.quantile(y, np.linspace(0.2, 0.8, n_states))
    means = np.asarray(qs, dtype=np.float64)
    vars_ = np.full(n_states, max(float(y.var()), 1e-6), dtype=np.float64)
    start = np.full(n_states, 1.0 / n_states, dtype=np.float64)
    trans = 0.85 * np.eye(n_states) + 0.15 / n_states
    trans = trans / trans.sum(axis=1, keepdims=True)
    _ = seed
    for _i in range(n_iter):
        gamma = _forward_backward(y, means, vars_, start, trans)
        nk = np.clip(gamma.sum(axis=0), 1e-8, None)
        means = (gamma.T @ y) / nk
        for k in range(n_states):
            vars_[k] = max(float(np.sum(gamma[:, k] * (y - means[k]) ** 2) / nk[k]), 1e-8)
        start = gamma[0] / max(float(gamma[0].sum()), 1e-8)
        # stay-biased transitions from posterior occupancy
        for i in range(n_states):
            for j in range(n_states):
                trans[i, j] = 0.85 if i == j else 0.15 / max(n_states - 1, 1)
        trans = trans / trans.sum(axis=1, keepdims=True)
    return means, vars_, start, trans


def _log_emit(y: np.ndarray, means: np.ndarray, vars_: np.ndarray) -> np.ndarray:
    t_len = len(y)
    k = len(means)
    out = np.zeros((t_len, k), dtype=np.float64)
    for t in range(t_len):
        for j in range(k):
            v = max(float(vars_[j]), 1e-12)
            out[t, j] = -0.5 * (
                math.log(2.0 * math.pi * v) + (float(y[t]) - float(means[j])) ** 2 / v
            )
    return out


def _logsumexp(row: np.ndarray) -> float:
    m = float(np.max(row))
    return m + math.log(float(np.sum(np.exp(row - m))))


def _forward_backward(
    y: np.ndarray,
    means: np.ndarray,
    vars_: np.ndarray,
    start: np.ndarray,
    trans: np.ndarray,
) -> np.ndarray:
    emit = _log_emit(y, means, vars_)
    t_len, k = emit.shape
    log_trans = np.log(np.clip(trans, 1e-12, 1.0))
    log_alpha = np.zeros((t_len, k), dtype=np.float64)
    log_alpha[0] = np.log(np.clip(start, 1e-12, 1.0)) + emit[0]
    for t in range(1, t_len):
        for j in range(k):
            log_alpha[t, j] = emit[t, j] + _logsumexp(log_alpha[t - 1] + log_trans[:, j])
    log_beta = np.zeros((t_len, k), dtype=np.float64)
    for t in range(t_len - 2, -1, -1):
        for i in range(k):
            log_beta[t, i] = _logsumexp(log_trans[i] + emit[t + 1] + log_beta[t + 1])
    log_gamma = log_alpha + log_beta
    for t in range(t_len):
        log_gamma[t] -= _logsumexp(log_gamma[t])
    return np.exp(log_gamma)


def _forward_posterior(
    y: np.ndarray,
    means: np.ndarray,
    vars_: np.ndarray,
    start: np.ndarray,
    trans: np.ndarray,
) -> np.ndarray:
    emit = _log_emit(y, means, vars_)
    t_len, k = emit.shape
    log_trans = np.log(np.clip(trans, 1e-12, 1.0))
    log_alpha = np.zeros((t_len, k), dtype=np.float64)
    log_alpha[0] = np.log(np.clip(start, 1e-12, 1.0)) + emit[0]
    for t in range(1, t_len):
        for j in range(k):
            log_alpha[t, j] = emit[t, j] + _logsumexp(log_alpha[t - 1] + log_trans[:, j])
    post = np.zeros_like(log_alpha)
    for t in range(t_len):
        row = log_alpha[t] - _logsumexp(log_alpha[t])
        post[t] = np.exp(row)
    return post


def _viterbi(
    y: np.ndarray,
    means: np.ndarray,
    vars_: np.ndarray,
    start: np.ndarray,
    trans: np.ndarray,
) -> list[int]:
    emit = _log_emit(y, means, vars_)
    t_len, k = emit.shape
    log_trans = np.log(np.clip(trans, 1e-12, 1.0))
    delta = np.zeros((t_len, k), dtype=np.float64)
    psi = np.zeros((t_len, k), dtype=np.int64)
    delta[0] = np.log(np.clip(start, 1e-12, 1.0)) + emit[0]
    for t in range(1, t_len):
        for j in range(k):
            scores = delta[t - 1] + log_trans[:, j]
            psi[t, j] = int(np.argmax(scores))
            delta[t, j] = float(scores[psi[t, j]]) + emit[t, j]
    path = [0] * t_len
    path[-1] = int(np.argmax(delta[-1]))
    for t in range(t_len - 2, -1, -1):
        path[t] = int(psi[t + 1, path[t + 1]])
    return path
