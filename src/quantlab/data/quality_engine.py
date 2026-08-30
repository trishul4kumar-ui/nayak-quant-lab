"""Quality severity report. Never silently repair raw records."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from quantlab.domain.research import CheckResult


class QualitySeverity(StrEnum):
    INFO = "info"
    WARN = "warn"
    ERROR = "error"
    FAIL = "fail"
    NOT_TESTED = "not_tested"


class QualityIssue(BaseModel):
    model_config = ConfigDict(frozen=True)

    dimension: str
    severity: QualitySeverity
    detail: str


class ProductionQualityReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    completeness: CheckResult = CheckResult.NOT_TESTED
    uniqueness: CheckResult = CheckResult.NOT_TESTED
    validity: CheckResult = CheckResult.NOT_TESTED
    temporal_consistency: CheckResult = CheckResult.NOT_TESTED
    cross_source_consistency: CheckResult = CheckResult.NOT_TESTED
    identity_consistency: CheckResult = CheckResult.NOT_TESTED
    corporate_action_consistency: CheckResult = CheckResult.NOT_TESTED
    calendar_consistency: CheckResult = CheckResult.NOT_TESTED
    pit_availability: CheckResult = CheckResult.NOT_TESTED
    survivorship: CheckResult = CheckResult.NOT_TESTED
    adjustment_integrity: CheckResult = CheckResult.NOT_TESTED
    issues: list[QualityIssue] = Field(default_factory=list)
    note: str = "Missing evidence is NOT_TESTED, not PASS."


def report_from_counts(
    *,
    rows: int,
    duplicates: int,
    invalid: int,
    pit_ok: bool | None,
) -> ProductionQualityReport:
    issues: list[QualityIssue] = []
    uniqueness = CheckResult.PASS if duplicates == 0 else CheckResult.FAIL
    validity = CheckResult.PASS if invalid == 0 else CheckResult.FAIL
    completeness = CheckResult.PASS if rows > 0 else CheckResult.NOT_TESTED
    if duplicates:
        issues.append(
            QualityIssue(
                dimension="uniqueness",
                severity=QualitySeverity.FAIL,
                detail=str(duplicates),
            )
        )
    if invalid:
        issues.append(
            QualityIssue(dimension="validity", severity=QualitySeverity.FAIL, detail=str(invalid))
        )
    pit = (
        CheckResult.NOT_TESTED
        if pit_ok is None
        else CheckResult.PASS
        if pit_ok
        else CheckResult.FAIL
    )
    return ProductionQualityReport(
        completeness=completeness,
        uniqueness=uniqueness,
        validity=validity,
        pit_availability=pit,
        issues=issues,
    )
