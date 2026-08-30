"""Run-length / duration statistics. Not a forecast of remaining time in regime."""

from __future__ import annotations

from pydantic import BaseModel, Field

from quantlab.domain.research import CheckResult
from quantlab.regimes.detectors import RegimeObservation


class DurationReport(BaseModel):
    schema_version: str = "1"
    mean: dict[str, float] = Field(default_factory=dict)
    median: dict[str, float] = Field(default_factory=dict)
    n_runs: dict[str, int] = Field(default_factory=dict)
    status: CheckResult = CheckResult.PASS
    note: str = "run lengths of hard labels; not expected remaining duration"


def durations(observations: list[RegimeObservation]) -> DurationReport:
    runs: dict[str, list[int]] = {}
    current: str | None = None
    length = 0
    for obs in observations:
        label = obs.hard_label
        if label is None:
            if current is not None and length:
                runs.setdefault(current, []).append(length)
            current, length = None, 0
            continue
        if label == current:
            length += 1
            continue
        if current is not None and length:
            runs.setdefault(current, []).append(length)
        current, length = label, 1
    if current is not None and length:
        runs.setdefault(current, []).append(length)
    if not runs:
        return DurationReport(status=CheckResult.NOT_TESTED, note="no labelled runs")
    mean = {k: sum(v) / len(v) for k, v in sorted(runs.items())}
    median = {k: float(sorted(v)[len(v) // 2]) for k, v in sorted(runs.items())}
    n_runs = {k: len(v) for k, v in sorted(runs.items())}
    return DurationReport(mean=mean, median=median, n_runs=n_runs)
