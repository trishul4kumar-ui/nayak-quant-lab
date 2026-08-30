"""Compare candidates without ranking by Sharpe alone."""

from __future__ import annotations

from pydantic import BaseModel, Field

from quantlab.orchestration.selection import CandidateOutcome


class ComparisonRow(BaseModel):
    candidate_id: str
    lookback: int
    cost_bps: float
    total_return: float | None
    sharpe: float | None
    max_drawdown: float | None
    selected: bool
    failed: bool
    note: str = "do not rank by Sharpe alone"


class ComparisonReport(BaseModel):
    schema_version: str = "1"
    rows: list[ComparisonRow] = Field(default_factory=list)
    note: str = "FACT vs MEASUREMENT vs INTERPRETATION stay distinct"


def compare_candidates(outcomes: list[CandidateOutcome]) -> ComparisonReport:
    rows = [
        ComparisonRow(
            candidate_id=item.candidate_id,
            lookback=item.lookback,
            cost_bps=item.cost_bps,
            total_return=item.total_return,
            sharpe=item.sharpe,
            max_drawdown=item.max_drawdown,
            selected=item.selected,
            failed=item.failed,
        )
        for item in outcomes
    ]
    return ComparisonReport(rows=rows)
