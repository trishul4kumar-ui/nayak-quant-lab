"""Sensitivity of recorded candidates. Does not invent a second robustness engine."""

from __future__ import annotations

from pydantic import BaseModel, Field

from quantlab.orchestration.selection import CandidateOutcome


class SensitivityRow(BaseModel):
    parameter: str
    left: float
    right: float
    metric_left: float | None
    metric_right: float | None


class SensitivityReport(BaseModel):
    schema_version: str = "1"
    rows: list[SensitivityRow] = Field(default_factory=list)
    note: str = "Sensitivity is MEASUREMENT. It is not a second search."


def cost_sensitivity(outcomes: list[CandidateOutcome], *, lookback: int = 20) -> SensitivityReport:
    ten = _match(outcomes, lookback=lookback, cost_bps=10.0)
    twenty = _match(outcomes, lookback=lookback, cost_bps=20.0)
    return SensitivityReport(
        rows=[
            SensitivityRow(
                parameter="cost_bps",
                left=10.0,
                right=20.0,
                metric_left=None if ten is None else ten.total_return,
                metric_right=None if twenty is None else twenty.total_return,
            )
        ]
    )


def _match(
    outcomes: list[CandidateOutcome], *, lookback: int, cost_bps: float
) -> CandidateOutcome | None:
    for item in outcomes:
        if (
            item.lookback == lookback
            and abs(item.cost_bps - cost_bps) < 1e-12
            and item.strategy_id == "cs_momentum_v1"
        ):
            return item
    return None
