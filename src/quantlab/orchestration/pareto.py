"""Non-dominated family view. Not a Sharpe leaderboard."""

from __future__ import annotations

from pydantic import BaseModel, Field

from quantlab.orchestration.selection import CandidateOutcome


class ParetoPoint(BaseModel):
    candidate_id: str
    total_return: float
    max_drawdown: float
    cost_bps: float
    dominated: bool


class ParetoReport(BaseModel):
    schema_version: str = "1"
    points: list[ParetoPoint] = Field(default_factory=list)
    note: str = "Pareto is descriptive. It does not override the research gate."


def pareto_front(outcomes: list[CandidateOutcome]) -> ParetoReport:
    usable = [
        item for item in outcomes if item.total_return is not None and item.max_drawdown is not None
    ]
    points: list[ParetoPoint] = []
    for item in usable:
        ret = item.total_return
        dd = item.max_drawdown
        if ret is None or dd is None:
            continue
        dominated = False
        for other in usable:
            if other.candidate_id == item.candidate_id:
                continue
            other_ret = other.total_return
            other_dd = other.max_drawdown
            if other_ret is None or other_dd is None:
                continue
            better_ret = other_ret >= ret
            better_dd = other_dd <= dd
            better_cost = other.cost_bps <= item.cost_bps
            strictly = other_ret > ret or other_dd < dd or other.cost_bps < item.cost_bps
            if better_ret and better_dd and better_cost and strictly:
                dominated = True
                break
        points.append(
            ParetoPoint(
                candidate_id=item.candidate_id,
                total_return=ret,
                max_drawdown=dd,
                cost_bps=item.cost_bps,
                dominated=dominated,
            )
        )
    return ParetoReport(points=points)
