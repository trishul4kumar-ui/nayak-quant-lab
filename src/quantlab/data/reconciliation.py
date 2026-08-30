"""Multi-source reconciliation. Never auto-pick the most favorable value."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class ResolutionStatus(StrEnum):
    MATCHED = "matched"
    WITHIN_TOLERANCE = "within_tolerance"
    UNRESOLVED = "unresolved"
    NOT_TESTED = "not_tested"


class SourceDifference(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_a: str
    source_b: str
    field: str
    value_a: float | None
    value_b: float | None
    difference: float | None
    tolerance: float
    resolution_policy: str
    resolution_status: ResolutionStatus
    note: str = "Unresolved discrepancy is a visible data-quality issue."


def compare_closes(
    *,
    source_a: str,
    source_b: str,
    close_a: float,
    close_b: float,
    tolerance: float,
    policy: str = "record_only",
) -> SourceDifference:
    delta = abs(close_a - close_b)
    if delta == 0:
        status = ResolutionStatus.MATCHED
    elif delta <= tolerance:
        status = ResolutionStatus.WITHIN_TOLERANCE
    else:
        status = ResolutionStatus.UNRESOLVED
    return SourceDifference(
        source_a=source_a,
        source_b=source_b,
        field="close",
        value_a=close_a,
        value_b=close_b,
        difference=delta,
        tolerance=tolerance,
        resolution_policy=policy,
        resolution_status=status,
    )
