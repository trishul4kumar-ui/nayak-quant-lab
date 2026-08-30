"""Guided Test wizard strategy templates."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StrategyTemplate:
    template_id: str
    name: str
    summary: str
    hypothesis: str
    runnable: bool
    lookback: int = 20
    top_n: int = 2
    cost_bps: float = 10.0
    n_days: int = 80


TEMPLATES: tuple[StrategyTemplate, ...] = (
    StrategyTemplate(
        template_id="cs_momentum_v1",
        name="Cross-sectional momentum",
        summary="Rank by 20-day momentum, hold top names — the default lab strategy.",
        hypothesis="Higher 20-day momentum predicts next-bar return after costs.",
        runnable=True,
    ),
    StrategyTemplate(
        template_id="mean_reversion_stub",
        name="Mean reversion (preview)",
        summary="Buy recent losers — template UI only; engine still runs momentum in this build.",
        hypothesis="Short-term losers revert on the next bar after costs.",
        runnable=False,
        lookback=10,
        top_n=3,
    ),
    StrategyTemplate(
        template_id="blank_hypothesis",
        name="Blank hypothesis",
        summary="Same momentum engine with your own journal framing — customize the note, not the code yet.",
        hypothesis="Describe your idea in the journal after the run.",
        runnable=True,
        lookback=20,
        top_n=2,
    ),
)


def template_by_id(template_id: str) -> StrategyTemplate:
    for template in TEMPLATES:
        if template.template_id == template_id:
            return template
    return TEMPLATES[0]
