"""PIT covariance estimators. Future realized returns never enter Σ(T)."""

from __future__ import annotations

from datetime import datetime

import numpy as np
from pydantic import BaseModel, Field

from quantlab.backtest.spec import config_hash
from quantlab.core.errors import CovarianceError
from quantlab.core.identifiers import InstrumentId
from quantlab.domain.models import OHLCVBar
from quantlab.domain.research import CheckResult
from quantlab.features.engine import pit_bars
from quantlab.math.metrics import simple_returns
from quantlab.research.cache import ResultCache


class CovarianceReport(BaseModel):
    schema_version: str = "1"
    names: list[str] = Field(default_factory=list)
    matrix: list[list[float]] = Field(default_factory=list)
    lookback: int = 0
    estimator: str = "sample"
    as_of: datetime | None = None
    n_obs: int = 0
    min_eigenvalue: float | None = None
    condition_number: float | None = None
    rank: int | None = None
    psd: bool = False
    repair: str = "none"
    shrinkage: float | None = None
    ewma_lambda: float | None = None
    status: CheckResult = CheckResult.NOT_TESTED
    note: str = "PIT-available simple returns; ddof=0 for sample"


def pit_return_matrix(
    bars: dict[InstrumentId, list[OHLCVBar]],
    as_of: datetime,
    names: list[str],
    lookback: int,
) -> tuple[list[str], np.ndarray]:
    if lookback < 2:
        raise CovarianceError("covariance lookback must be >= 2 sessions")
    columns: list[list[float]] = []
    kept: list[str] = []
    for name in names:
        inst = InstrumentId.parse(name)
        series = bars.get(inst)
        if series is None:
            continue
        available = pit_bars(series, as_of)
        rets = simple_returns([b.close for b in available])
        if len(rets) < lookback:
            continue
        columns.append(rets[-lookback:])
        kept.append(name)
    if len(kept) < 2:
        raise CovarianceError("need at least two names with sufficient PIT history")
    arr = np.asarray(columns, dtype=np.float64).T
    if not np.isfinite(arr).all():
        raise CovarianceError("non-finite returns in covariance window")
    return kept, arr


def sample_covariance(
    bars: dict[InstrumentId, list[OHLCVBar]],
    as_of: datetime,
    names: list[str],
    lookback: int,
    *,
    repair: str = "none",
) -> CovarianceReport:
    return estimate_covariance(bars, as_of, names, lookback, estimator="sample", repair=repair)


def estimate_covariance(
    bars: dict[InstrumentId, list[OHLCVBar]],
    as_of: datetime,
    names: list[str],
    lookback: int,
    *,
    estimator: str = "sample",
    repair: str = "none",
    ewma_lambda: float = 0.94,
    shrinkage: float = 0.2,
) -> CovarianceReport:
    kept, arr = pit_return_matrix(bars, as_of, names, lookback)
    if estimator == "sample":
        cov = np.cov(arr, rowvar=False, ddof=0)
        extra: dict[str, float | None] = {}
        note = "sample covariance of PIT-available simple returns; ddof=0"
    elif estimator == "ewma":
        if not 0.0 < ewma_lambda < 1.0:
            raise CovarianceError("ewma_lambda must be in (0, 1)")
        cov = _ewma(arr, ewma_lambda)
        extra = {"ewma_lambda": ewma_lambda}
        note = f"EWMA covariance λ={ewma_lambda} on PIT returns"
    elif estimator == "shrinkage":
        if not 0.0 <= shrinkage <= 1.0:
            raise CovarianceError("shrinkage intensity must be in [0, 1]")
        sample = np.cov(arr, rowvar=False, ddof=0)
        target = np.diag(np.diag(sample))
        cov = (1.0 - shrinkage) * sample + shrinkage * target
        extra = {"shrinkage": shrinkage}
        note = f"sample shrunk toward diagonal; intensity={shrinkage}"
    else:
        raise CovarianceError(f"unknown covariance estimator {estimator}")
    return _finalize(
        cov,
        kept,
        lookback=lookback,
        estimator=estimator,
        as_of=as_of,
        n_obs=lookback,
        repair=repair,
        extra=extra,
        note=note,
    )


def covariance_cache_key(
    *,
    snapshot_id: str,
    names: list[str],
    as_of: datetime,
    lookback: int,
    estimator: str,
    repair: str,
    ewma_lambda: float,
    shrinkage: float,
) -> str:
    return config_hash(
        {
            "covariance_implementation": "spectral-tolerance-v2",
            "snapshot_id": snapshot_id,
            "names": sorted(names),
            "as_of": as_of.isoformat(),
            "lookback": lookback,
            "estimator": estimator,
            "repair": repair,
            "ewma_lambda": ewma_lambda,
            "shrinkage": shrinkage,
        }
    )


COVARIANCE_CACHE = ResultCache()


def principal_risk_shares(report: CovarianceReport) -> list[float]:
    eigs = np.linalg.eigvalsh(as_array(report))
    positive = np.clip(eigs, 0.0, None)
    total = float(positive.sum())
    if total <= 0:
        return []
    ordered = np.sort(positive)[::-1]
    return [float(v / total) for v in ordered.tolist()]


def as_array(report: CovarianceReport) -> np.ndarray:
    return np.asarray(report.matrix, dtype=np.float64)


def _ewma(arr: np.ndarray, lam: float) -> np.ndarray:
    n_obs, _n = arr.shape
    weights = np.array(
        [(1.0 - lam) * lam ** (n_obs - 1 - t) for t in range(n_obs)], dtype=np.float64
    )
    weights = weights / float(weights.sum())
    mu = weights @ arr
    centered = arr - mu
    return np.asarray((centered * weights[:, None]).T @ centered, dtype=np.float64)


def _finalize(
    cov: np.ndarray,
    names: list[str],
    *,
    lookback: int,
    estimator: str,
    as_of: datetime,
    n_obs: int,
    repair: str,
    extra: dict[str, float | None],
    note: str,
) -> CovarianceReport:
    if cov.shape != (len(names), len(names)) or not np.isfinite(cov).all():
        raise CovarianceError("covariance must be a finite square matrix matching names")
    cov = 0.5 * (cov + cov.T)
    eigs = np.linalg.eigvalsh(cov)
    min_eig = float(eigs[0])
    max_eig = float(eigs[-1])
    psd = min_eig >= -1e-10
    used_repair = "none"
    if not psd:
        if repair != "eigenvalue_clip":
            raise CovarianceError(f"covariance not PSD; min_eig={min_eig}")
        evals, evecs = np.linalg.eigh(cov)
        clipped = np.clip(evals, 0.0, None)
        cov = evecs @ np.diag(clipped) @ evecs.T
        cov = 0.5 * (cov + cov.T)
        eigs = np.linalg.eigvalsh(cov)
        min_eig = float(eigs[0])
        max_eig = float(eigs[-1])
        psd = min_eig >= -1e-10
        used_repair = "eigenvalue_clip"
    # A null eigenvalue can land a few ulps on either side of zero depending
    # on LAPACK/platform. Use the same scale-aware threshold for rank and
    # invertibility; never turn that rounding noise into a huge condition number.
    tolerance = np.finfo(np.float64).eps * len(eigs) * max(abs(max_eig), abs(min_eig))
    rank = int(np.sum(eigs > tolerance))
    cond = None if min_eig <= tolerance else max_eig / min_eig
    # Retain rejection of genuinely ill-scaled asset variances even when a
    # positive variance is below the spectral resolution of the whole matrix.
    positive_variances = np.diag(cov)[np.diag(cov) > 0]
    if len(positive_variances) > 1 and (
        float(positive_variances.max()) / float(positive_variances.min()) > 1e12
    ):
        raise CovarianceError("ill-conditioned covariance; asset variance scale exceeds limit")
    if cond is not None and cond > 1e12:
        raise CovarianceError(f"ill-conditioned covariance; cond={cond}")
    if rank < len(names):
        note += "; numerically singular PSD matrix; not directly invertible"
    return CovarianceReport(
        names=names,
        matrix=[[float(x) for x in row] for row in cov.tolist()],
        lookback=lookback,
        estimator=estimator,
        as_of=as_of,
        n_obs=n_obs,
        min_eigenvalue=min_eig,
        condition_number=cond,
        rank=rank,
        psd=psd,
        repair=used_repair,
        shrinkage=extra.get("shrinkage"),
        ewma_lambda=extra.get("ewma_lambda"),
        status=CheckResult.PASS,
        note=note,
    )
