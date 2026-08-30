"""Walk-forward clustering. Full-sample clustering is retrospective only."""

from __future__ import annotations

import numpy as np

from quantlab.core.errors import RegimeError
from quantlab.domain.research import CheckResult
from quantlab.regimes.definition import RegimeModel
from quantlab.regimes.detectors import RegimeObservation
from quantlab.regimes.normalize import series_of
from quantlab.regimes.snapshot import StateSnapshot


def classify_clusters(
    model: RegimeModel,
    snapshots: list[StateSnapshot],
    *,
    predictive: bool = True,
) -> list[RegimeObservation]:
    field = model.state_features[0] if model.state_features else "realized_vol_20"
    raw = series_of(snapshots, field)
    k = int(model.parameters.get("k", 2))
    seed = int(model.parameters.get("seed", 0))
    min_obs = model.min_obs
    if model.detector.value == "cluster_full_sample":
        if predictive:
            raise RegimeError("full-sample clustering is not a historical predictive feature")
        labels = _full_sample(raw, k, seed, min_obs)
        return _rows(snapshots, labels, "cluster_full_sample", retrospective=True)
    labels = _walk_forward(raw, k, seed, min_obs)
    return _rows(snapshots, labels, "cluster_walk_forward", retrospective=False)


def _walk_forward(
    raw: list[float | None],
    k: int,
    seed: int,
    min_obs: int,
) -> list[int | None]:
    hist: list[float] = []
    out: list[int | None] = []
    for value in raw:
        if value is None:
            out.append(None)
            continue
        hist.append(value)
        if len(hist) < min_obs:
            out.append(None)
            continue
        out.append(_assign_last(np.asarray(hist, dtype=np.float64), k, seed))
    return out


def _full_sample(
    raw: list[float | None],
    k: int,
    seed: int,
    min_obs: int,
) -> list[int | None]:
    finite = [v for v in raw if v is not None]
    if len(finite) < min_obs:
        return [None] * len(raw)
    arr = np.asarray(finite, dtype=np.float64)
    centers = _centers(arr, k, seed)
    assigned = [_nearest(v, centers) for v in arr]
    out: list[int | None] = []
    j = 0
    for value in raw:
        if value is None:
            out.append(None)
        else:
            out.append(assigned[j])
            j += 1
    return out


def _assign_last(hist: np.ndarray, k: int, seed: int) -> int:
    centers = _centers(hist, k, seed)
    return _nearest(float(hist[-1]), centers)


def _centers(hist: np.ndarray, k: int, seed: int) -> np.ndarray:
    qs = np.quantile(hist, np.linspace(0.25, 0.75, k))
    centers = np.asarray(qs, dtype=np.float64)
    _ = seed
    for _i in range(8):
        assign = np.array([_nearest(float(x), centers) for x in hist])
        for j in range(k):
            members = hist[assign == j]
            if len(members):
                centers[j] = float(members.mean())
    return centers


def _nearest(value: float, centers: np.ndarray) -> int:
    return int(np.argmin(np.abs(centers - value)))


def _rows(
    snapshots: list[StateSnapshot],
    labels: list[int | None],
    method: str,
    *,
    retrospective: bool,
) -> list[RegimeObservation]:
    rows: list[RegimeObservation] = []
    for snap, label in zip(snapshots, labels, strict=True):
        hard = None if label is None else f"cluster_{label}"
        rows.append(
            RegimeObservation(
                as_of=snap.as_of,
                hard_label=hard,
                probabilities={} if hard is None else {hard: 1.0},
                confidence=None if hard is None else 1.0,
                method=method,
                retrospective=retrospective,
                status=CheckResult.NOT_TESTED if hard is None else CheckResult.PASS,
                note=(
                    "retrospective full-sample clusters"
                    if retrospective
                    else "walk-forward assignment using history through T"
                ),
            )
        )
    return rows
