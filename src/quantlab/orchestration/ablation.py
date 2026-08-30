"""Ablation: remove one component and record the change. Missing a cell is a FAIL."""

from __future__ import annotations

from pydantic import BaseModel, Field

from quantlab.orchestration.selection import CandidateOutcome


class AblationRow(BaseModel):
    component: str
    with_component: float | None
    without_component: float | None
    delta: float | None
    note: str = "Ablation is diagnostic, not a promotion score."


class AblationReport(BaseModel):
    schema_version: str = "1"
    rows: list[AblationRow] = Field(default_factory=list)
    note: str = "FACT: which component was removed. INTERPRETATION is separate."


def ablating_lookback(
    outcomes: list[CandidateOutcome],
    *,
    cost_bps: float = 10.0,
    long_lookback: int = 20,
    short_lookback: int = 5,
) -> AblationReport:
    long_c = _match(outcomes, lookback=long_lookback, cost_bps=cost_bps)
    short_c = _match(outcomes, lookback=short_lookback, cost_bps=cost_bps)
    long_v = None if long_c is None else long_c.total_return
    short_v = None if short_c is None else short_c.total_return
    delta = None if long_v is None or short_v is None else long_v - short_v
    return AblationReport(
        rows=[
            AblationRow(
                component=f"momentum_lookback_{long_lookback}",
                with_component=long_v,
                without_component=short_v,
                delta=delta,
                note="short lookback is the ablation, not a new secret search",
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
