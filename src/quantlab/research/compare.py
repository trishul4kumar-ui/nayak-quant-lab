"""Compare experiments on several axes. Never rank by one metric."""

from __future__ import annotations

from pydantic import BaseModel, Field

from quantlab.domain.models import ExperimentRun


class ComparisonRow(BaseModel):
    experiment_id: str
    name: str
    data_kind: str
    total_return: float | None
    sharpe: float | None
    max_drawdown: float | None
    mean_turnover: float | None
    cost_bps: float
    gate_outcome: str
    look_ahead: str


class ComparisonReport(BaseModel):
    schema_version: str = "1"
    rows: list[ComparisonRow] = Field(default_factory=list)
    note: str = "do not rank by Sharpe alone"


def compare_runs(runs: list[ExperimentRun]) -> ComparisonReport:
    rows: list[ComparisonRow] = []
    for run in runs:
        rows.append(
            ComparisonRow(
                experiment_id=run.id,
                name=run.name,
                data_kind=run.data_kind,
                total_return=run.metrics.get("total_return"),
                sharpe=run.metrics.get("sharpe"),
                max_drawdown=run.metrics.get("max_drawdown"),
                mean_turnover=run.metrics.get("mean_turnover"),
                cost_bps=run.transaction_cost_bps,
                gate_outcome=run.gate_outcome,
                look_ahead=run.integrity.get("look_ahead_bias", ""),
            )
        )
    return ComparisonReport(rows=rows)
