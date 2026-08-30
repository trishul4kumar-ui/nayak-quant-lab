"""Half-life of a rolling IC series. Distinct from horizon IC decay in quantlab.alpha.decay."""

from __future__ import annotations

import math

from quantlab.adaptive.state import DecayEstimate, DecayStatus


def estimate_half_life(ics: list[float], min_obs: int = 12) -> DecayEstimate:
    n = len(ics)
    if n < min_obs:
        return DecayEstimate(
            method="linear_ols",
            sample_size=n,
            status=DecayStatus.INSUFFICIENT_DATA,
            warnings=["need more realized IC points"],
        )
    xs = list(range(n))
    mx = (n - 1) / 2.0
    my = sum(ics) / n
    num = sum((xs[i] - mx) * (ics[i] - my) for i in range(n))
    den = sum((xs[i] - mx) ** 2 for i in range(n))
    if den <= 0:
        return DecayEstimate(method="linear_ols", sample_size=n, status=DecayStatus.UNSTABLE)
    slope = num / den
    intercept = my - slope * mx
    ss_tot = sum((v - my) ** 2 for v in ics)
    ss_res = sum((ics[i] - (intercept + slope * xs[i])) ** 2 for i in range(n))
    r2 = None if ss_tot <= 0 else 1.0 - ss_res / ss_tot
    if intercept <= 0 or slope >= 0:
        return DecayEstimate(
            method="linear_ols",
            estimate=None,
            sample_size=n,
            fit_quality=r2,
            status=DecayStatus.UNSTABLE,
            warnings=["fitted IC does not decay through half of intercept"],
            note="slope>=0 or intercept<=0; half-life not manufactured",
        )
    half = (intercept / 2.0 - intercept) / slope
    if half <= 0 or not math.isfinite(half):
        return DecayEstimate(
            method="linear_ols",
            sample_size=n,
            fit_quality=r2,
            status=DecayStatus.UNSTABLE,
        )
    if r2 is not None and r2 < 0.2:
        return DecayEstimate(
            method="linear_ols",
            estimate=float(half),
            sample_size=n,
            fit_quality=r2,
            status=DecayStatus.UNSTABLE,
            warnings=["low R^2; treat half-life as descriptive only"],
        )
    se_slope = math.sqrt(ss_res / max(n - 2, 1) / den)
    lo = None
    hi = None
    if se_slope > 0 and slope + 1.96 * se_slope < 0:
        slo = slope - 1.96 * se_slope
        shi = slope + 1.96 * se_slope
        lo = (intercept / 2.0 - intercept) / shi
        hi = (intercept / 2.0 - intercept) / slo
        if lo > hi:
            lo, hi = hi, lo
    return DecayEstimate(
        method="linear_ols",
        estimate=float(half),
        confidence_interval=None if lo is None or hi is None else (float(lo), float(hi)),
        sample_size=n,
        fit_quality=r2,
        status=DecayStatus.ESTIMABLE,
        note="sessions until fitted linear IC reaches half of intercept; not exponential truth",
    )
