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
    row = last_validation_row(runtime)
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
    passed = sum(1 for v in reasons.values() if str(v).lower() in {"pass", "passed", "ok", "true"})
    total = len(reasons)

    if isinstance(sharpe, float):
        target = 1.0
        if sharpe >= target:
            profit_line = f"Sharpe {sharpe:.2f} — at or above {target:.1f} target"
            profit_tone = "ok"
        else:
            gap = target - sharpe
            profit_line = f"Sharpe {sharpe:.2f} — {gap:.2f} below {target:.1f} target"
            profit_tone = "warn"
    else:
        profit_line = "Sharpe unavailable — review equity curve"
        profit_tone = "warn"

    if gate == "pass":
        rules_line = f"All {total} gate checks passed — rules intact"
        rules_tone = "ok"
    elif total:
        failed = total - passed
        rules_line = f"{failed} of {total} gate checks failing — review before live"
        rules_tone = "bad" if failed > 0 else "warn"
    else:
        rules_line = "Gate reasons not recorded — inspect summary table"
        rules_tone = "warn"

    return ValidationTwoQuestions(
        profit_line=profit_line,
        profit_tone=profit_tone,
        rules_line=rules_line,
        rules_tone=rules_tone,
    )
