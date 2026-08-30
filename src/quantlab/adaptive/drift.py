"""Concept-drift diagnostics on PIT IC history. Drift ≠ market regime."""

from __future__ import annotations

from pydantic import BaseModel, Field

from quantlab.adaptive.state import AdaptiveModelState, DriftStatus
from quantlab.domain.research import CheckResult


class DriftReport(BaseModel):
    schema_version: str = "1"
    status: DriftStatus = DriftStatus.INSUFFICIENT_DATA
    statistic: float | None = None
    n: int = 0
    transitions: list[str] = Field(default_factory=list)
    check: CheckResult = CheckResult.NOT_TESTED
    note: str = "IC drift is not a Prompt 09 regime label"


def classify_drift(
    ics: list[float], *, min_obs: int = 16, watch: float = 1.5, detect: float = 3.0
) -> DriftReport:
    if len(ics) < min_obs:
        return DriftReport(n=len(ics), note="insufficient IC history")
    hist: list[float] = []
    score = 0.0
    transitions: list[str] = []
    status = DriftStatus.STABLE
    for value in ics:
        if len(hist) < min_obs // 2:
            hist.append(value)
            continue
        mu = sum(hist) / len(hist)
        var = sum((x - mu) ** 2 for x in hist) / len(hist)
        sd = var**0.5
        if sd <= 0:
            hist.append(value)
            continue
        score = score + (value - mu) / sd
        if abs(score) >= detect:
            status = DriftStatus.DRIFT_DETECTED
            transitions.append("drift_detected")
            score = 0.0
        elif abs(score) >= watch and status is DriftStatus.STABLE:
            status = DriftStatus.WATCH
            transitions.append("watch")
        hist.append(value)
    return DriftReport(
        status=status,
        statistic=score,
        n=len(ics),
        transitions=transitions,
        check=CheckResult.PASS,
        note="CUSUM on realized IC with expanding mean through t-1; not a regime",
    )


def attach_drift(state: AdaptiveModelState, report: DriftReport) -> AdaptiveModelState:
    return state.model_copy(update={"drift_status": report.status})
