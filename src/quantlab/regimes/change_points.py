"""Change-point flags. A change-point is not a regime."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from quantlab.domain.research import CheckResult
from quantlab.regimes.normalize import series_of
from quantlab.regimes.snapshot import StateSnapshot


class ChangePoint(BaseModel):
    as_of: datetime
    statistic: float
    flagged: bool
    note: str = "change-point flag, not a regime label"


class ChangePointReport(BaseModel):
    schema_version: str = "1"
    points: list[ChangePoint] = Field(default_factory=list)
    n_flagged: int = 0
    status: CheckResult = CheckResult.PASS
    note: str = "CUSUM on EW returns with expanding mean through T-1; not a regime taxonomy"


def cusum_flags(
    snapshots: list[StateSnapshot],
    threshold: float = 3.0,
    min_obs: int = 10,
) -> ChangePointReport:
    values = series_of(snapshots, "market_ew_return")
    hist: list[float] = []
    score = 0.0
    points: list[ChangePoint] = []
    for snap, value in zip(snapshots, values, strict=True):
        if value is None:
            continue
        if len(hist) < min_obs:
            hist.append(value)
            points.append(
                ChangePoint(as_of=snap.as_of, statistic=0.0, flagged=False, note="warmup")
            )
            continue
        mu = sum(hist) / len(hist)
        var = sum((x - mu) ** 2 for x in hist) / len(hist)
        sd = var**0.5
        if sd <= 0:
            hist.append(value)
            points.append(
                ChangePoint(as_of=snap.as_of, statistic=0.0, flagged=False, note="zero variance")
            )
            continue
        score = score + (value - mu) / sd
        flagged = abs(score) >= threshold
        if flagged:
            score = 0.0
        hist.append(value)
        points.append(ChangePoint(as_of=snap.as_of, statistic=score, flagged=flagged))
    return ChangePointReport(points=points, n_flagged=sum(1 for p in points if p.flagged))
