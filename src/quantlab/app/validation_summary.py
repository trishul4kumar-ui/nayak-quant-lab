"""Validation page — two-question summary (Meridiem-style)."""

from __future__ import annotations

from dataclasses import dataclass

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.queries import last_validation_row


@dataclass(frozen=True)
class ValidationTwoQuestions:
    profit_line: str
    profit_tone: str
    rules_line: str
    rules_tone: str


def validation_two_questions(runtime: ApplicationRuntime) -> ValidationTwoQuestions:
    prefs = runtime.ui_settings.current
    row = last_validation_row(
        runtime,
        parent_run_id=str(getattr(prefs, "selected_backtest_id", "")) or None,
        candidate_id=str(getattr(prefs, "selected_candidate_id", "")) or None,
    )
    if row is None:
        return ValidationTwoQuestions(
            profit_line="No validation yet — run the suite after your first backtest.",
            profit_tone="neutral",
            rules_line="Rules checks appear here once validation completes.",
            rules_tone="neutral",
        )

    sharpe = row.get("sharpe")
    gate = str(row.get("gate_outcome") or "unknown").lower()
    reasons = row.get("gate_reasons") or {}
    checks = [str(value).lower() for key, value in reasons.items() if key != "outcome"]
    passed = sum(value in {"pass", "passed", "ok", "true"} for value in checks)
    failed = sum(value in {"fail", "failed", "reject"} for value in checks)
    warnings = sum(value in {"warn", "warning"} for value in checks)
    untested = sum(value in {"not_tested", "unknown", ""} for value in checks)
    total = len(checks)

    if isinstance(sharpe, float):
        profit_line = (
            f"Recorded OOS Sharpe {sharpe:.2f}. This estimate does not predict a profit target."
        )
        profit_tone = "neutral"
    else:
        profit_line = "Sharpe unavailable — review equity curve"
        profit_tone = "warn"

    if total:
        rules_line = (
            f"{passed}/{total} PASS · {failed} FAIL · {warnings} WARN · {untested} NOT_TESTED. "
            f"Research gate: {gate.upper()}; not live authorization."
        )
        rules_tone = "bad" if failed else "warn" if warnings or untested else "neutral"
    else:
        rules_line = "Gate reasons not recorded — inspect summary table"
        rules_tone = "warn"

    return ValidationTwoQuestions(
        profit_line=profit_line,
        profit_tone=profit_tone,
        rules_line=rules_line,
        rules_tone=rules_tone,
    )
