"""OLS factor regression. The intercept is a model estimate, not validated alpha."""

from __future__ import annotations

import numpy as np
from pydantic import BaseModel, Field

from quantlab.core.errors import FactorError
from quantlab.domain.research import CheckResult


class RegressionReport(BaseModel):
    schema_version: str = "1"
    names: list[str] = Field(default_factory=list)
    coefficients: list[float] = Field(default_factory=list)
    intercept: float | None = None
    intercept_label: str = "model intercept estimate"
    r_squared: float | None = None
    residual_std: float | None = None
    condition_number: float | None = None
    vif: list[float] = Field(default_factory=list)
    n: int = 0
    status: CheckResult = CheckResult.PASS
    note: str = "intercept is not automatically genuine alpha; Prompt 05 remains the gate"


def ols(
    y: list[float],
    columns: dict[str, list[float]],
    *,
    add_intercept: bool = True,
) -> RegressionReport:
    names = list(columns)
    if not names:
        raise FactorError("regression needs at least one factor column")
    n = len(y)
    if any(len(columns[k]) != n for k in names):
        raise FactorError("regression columns are misaligned")
    if n < len(names) + (1 if add_intercept else 0) + 1:
        return RegressionReport(
            names=names,
            n=n,
            status=CheckResult.NOT_TESTED,
            note="insufficient observations for OLS",
        )
    y_arr = np.asarray(y, dtype=np.float64)
    x_cols = [np.asarray(columns[k], dtype=np.float64) for k in names]
    x = np.column_stack(x_cols)
    if add_intercept:
        x = np.column_stack([np.ones(n), x])
    if not np.isfinite(x).all() or not np.isfinite(y_arr).all():
        raise FactorError("non-finite values in regression")
    try:
        beta, _residuals, _rank, _singular = np.linalg.lstsq(x, y_arr, rcond=None)
    except np.linalg.LinAlgError as exc:
        raise FactorError("OLS failed") from exc
    fitted = x @ beta
    resid = y_arr - fitted
    sst = float(np.sum((y_arr - y_arr.mean()) ** 2))
    sse = float(np.sum(resid**2))
    r2 = None if sst <= 0 else 1.0 - sse / sst
    intercept = float(beta[0]) if add_intercept else None
    coefs = [float(v) for v in (beta[1:] if add_intercept else beta)]
    xtx = x.T @ x
    eigs = np.linalg.eigvalsh(xtx)
    min_eig = float(eigs[0])
    max_eig = float(eigs[-1])
    cond = None if min_eig <= 0 else max_eig / min_eig
    vif = _vif(np.column_stack(x_cols))
    status = CheckResult.WARN if cond is not None and cond > 30 else CheckResult.PASS
    return RegressionReport(
        names=names,
        coefficients=coefs,
        intercept=intercept,
        r_squared=r2,
        residual_std=float(np.std(resid, ddof=0)),
        condition_number=cond,
        vif=vif,
        n=n,
        status=status,
        note=(
            "high condition number; coefficients are unstable"
            if status is CheckResult.WARN
            else "intercept is a model estimate, not validated alpha"
        ),
    )


def _vif(x: np.ndarray) -> list[float]:
    _, n_cols = x.shape
    out: list[float] = []
    for j in range(n_cols):
        y = x[:, j]
        others = np.delete(x, j, axis=1)
        if others.size == 0:
            out.append(1.0)
            continue
        others = np.column_stack([np.ones(len(y)), others])
        beta, _, _, _ = np.linalg.lstsq(others, y, rcond=None)
        fitted = others @ beta
        sst = float(np.sum((y - y.mean()) ** 2))
        sse = float(np.sum((y - fitted) ** 2))
        r2 = 0.0 if sst <= 0 else 1.0 - sse / sst
        out.append(float("inf") if r2 >= 1.0 else 1.0 / max(1.0 - r2, 1e-12))
    return out
