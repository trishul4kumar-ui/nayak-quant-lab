"""Robustness summary over recorded candidates. Prompt 05 remains authoritative."""

from __future__ import annotations

from pydantic import BaseModel

from quantlab.orchestration.selection import CandidateOutcome


class RobustnessReport(BaseModel):
    schema_version: str = "1"
    n_candidates: int
    n_positive_return: int
    min_return: float | None
    max_return: float | None
    note: str = (
        "Orchestration robustness is a family summary. "
        "Walk-forward / block-bootstrap remain Prompt 05."
    )


def robustness_summary(outcomes: list[CandidateOutcome]) -> RobustnessReport:
    values = [item.total_return for item in outcomes if item.total_return is not None]
    return RobustnessReport(
        n_candidates=len(outcomes),
        n_positive_return=sum(1 for v in values if v > 0),
        min_return=min(values) if values else None,
        max_return=max(values) if values else None,
    )
