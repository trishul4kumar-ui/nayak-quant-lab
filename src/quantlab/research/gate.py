"""Research promotion gate. No live-trading outcome exists in this phase."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from quantlab.domain.research import CheckResult


class GateOutcome(StrEnum):
    REJECT = "reject"
    WARN = "warn"
    RESEARCH_CANDIDATE = "research_candidate"
    PROMOTED_TO_PAPER = "promoted_to_paper"


class GateReason(BaseModel):
    name: str
    result: CheckResult
    required: bool
    note: str = ""


class ResearchGateResult(BaseModel):
    schema_version: str = "1"
    outcome: GateOutcome
    reasons: list[GateReason] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    def as_str_map(self) -> dict[str, str]:
        payload = {item.name: item.result.value for item in self.reasons}
        payload["outcome"] = self.outcome.value
        return payload


def evaluate_research_gate(
    *,
    integrity_failed: bool,
    next_bar_fill: bool,
    cost_bps: float,
    data_kind: str,
    walk_forward_windows: int,
    oos_sharpe: float | None,
    cost_still_positive_at_20bps: bool | None,
    parameter_fragile: bool,
    statistical_status: CheckResult,
    n_hypotheses: int,
    test_used_for_selection: bool,
) -> ResearchGateResult:
    reasons: list[GateReason] = []
    warnings: list[str] = []

    def add(name: str, result: CheckResult, required: bool, note: str = "") -> None:
        reasons.append(GateReason(name=name, result=result, required=required, note=note))

    add(
        "integrity",
        CheckResult.FAIL if integrity_failed else CheckResult.PASS,
        True,
        "FAIL cannot become a successful research result",
    )
    add(
        "next_bar_fill",
        CheckResult.PASS if next_bar_fill else CheckResult.FAIL,
        True,
    )
    add(
        "nonzero_costs",
        CheckResult.FAIL if cost_bps <= 0 else CheckResult.PASS,
        True,
        "zero-cost backtests are not tradability evidence",
    )
    if test_used_for_selection:
        add("test_set_sacred", CheckResult.FAIL, True, "test used for selection")
    else:
        add("test_set_sacred", CheckResult.PASS, True)

    if walk_forward_windows <= 0:
        add("walk_forward", CheckResult.NOT_TESTED, False, "no OOS windows")
    else:
        add("walk_forward", CheckResult.PASS, False, f"windows={walk_forward_windows}")

    if oos_sharpe is None:
        add("oos_evidence", CheckResult.NOT_TESTED, False)
    else:
        add("oos_evidence", CheckResult.WARN, False, f"oos_sharpe={oos_sharpe:.4f}")

    if cost_still_positive_at_20bps is None:
        add("cost_robustness", CheckResult.NOT_TESTED, False)
    elif cost_still_positive_at_20bps:
        add("cost_robustness", CheckResult.PASS, False)
    else:
        add("cost_robustness", CheckResult.WARN, False, "return collapsed at 20 bps")

    add(
        "parameter_stability",
        CheckResult.WARN if parameter_fragile else CheckResult.PASS,
        False,
        "isolated Sharpe peak" if parameter_fragile else "surface recorded",
    )
    add("statistical_evidence", statistical_status, False)
    add(
        "multiple_testing",
        CheckResult.WARN,
        False,
        f"n_hypotheses={n_hypotheses}",
    )

    if data_kind == "synthetic":
        add(
            "synthetic_not_market_evidence",
            CheckResult.WARN,
            True,
            "synthetic results cannot be promoted to paper",
        )
        warnings.append("data_kind=synthetic is architecture evidence only")

    if any(item.required and item.result is CheckResult.FAIL for item in reasons):
        outcome = GateOutcome.REJECT
    elif data_kind == "synthetic":
        outcome = GateOutcome.WARN
        warnings.append("no RESEARCH_CANDIDATE or paper promotion from synthetic data")
    elif any(item.result is CheckResult.FAIL for item in reasons):
        outcome = GateOutcome.REJECT
    elif any(item.result is CheckResult.WARN for item in reasons):
        outcome = GateOutcome.WARN
    elif walk_forward_windows > 0 and statistical_status is CheckResult.PASS:
        outcome = GateOutcome.RESEARCH_CANDIDATE
    else:
        outcome = GateOutcome.WARN

    return ResearchGateResult(outcome=outcome, reasons=reasons, warnings=warnings)
