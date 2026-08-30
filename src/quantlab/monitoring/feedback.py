"""Immutable research-feedback records. Not automatic hypotheses."""

from __future__ import annotations

from quantlab.backtest.spec import config_hash
from quantlab.monitoring.enums import AttributionMethod, DriftStatus, FeedbackKind
from quantlab.monitoring.models import (
    AttributionResult,
    DriftObservation,
    PnLBreakdown,
    ResearchFeedback,
)


def build_feedback(
    pnl: PnLBreakdown,
    attribution: AttributionResult,
    factor: AttributionResult,
    drift: DriftObservation,
    *,
    concentration: float,
    turnover: float,
) -> list[ResearchFeedback]:
    items: list[ResearchFeedback] = []

    def add(
        kind: FeedbackKind,
        observation: str,
        attribution_text: str,
        interpretation: str,
        question: str,
    ) -> None:
        payload: dict[str, object] = {
            "kind": kind.value,
            "observation": observation,
            "attribution": attribution_text,
            "interpretation": interpretation,
            "question": question,
        }
        items.append(
            ResearchFeedback(
                feedback_id=f"FB-{config_hash(payload)[:12]}",
                kind=kind,
                observation=observation,
                attribution=attribution_text,
                interpretation=interpretation,
                research_question=question,
            )
        )

    costs = pnl.costs or 0.0
    if pnl.pnl_total > 0 and costs > abs(pnl.pnl_total):
        add(
            FeedbackKind.EXECUTION_CONSUMED_EDGE,
            f"gross path positive ({pnl.pnl_total:.6f}) but costs {costs:.6f}",
            "execution/cost",
            "Gross P&L was consumed by simulated execution costs.",
            "Would a lower-turnover construction preserve more of the edge?",
        )
    if attribution.contributions:
        ranked = sorted(attribution.contributions, key=lambda r: abs(r.pnl), reverse=True)
        top = ranked[0]
        total_abs = sum(abs(r.pnl) for r in ranked) or 1.0
        if abs(top.pnl) / total_abs > 0.6:
            add(
                FeedbackKind.CONCENTRATED_SECURITY,
                f"{top.security_id} share {abs(top.pnl) / total_abs:.3f}",
                top.security_id,
                "Performance concentrated in one security.",
                "Is the result robust if that name is excluded?",
            )
    if (
        factor.method is not AttributionMethod.UNAVAILABLE
        and factor.factor_contributions
        and abs(factor.residual) < abs(pnl.pnl_total) * 0.3
    ):
        add(
            FeedbackKind.FACTOR_EXPLAINED,
            f"factor residual {factor.residual:.6f}",
            "factor",
            "Factor exposure explained most of the apparent P&L.",
            "Is residual alpha distinguishable from factor luck?",
        )
    if turnover > 0.5:
        add(
            FeedbackKind.TURNOVER_COSTS,
            f"turnover {turnover:.4f}",
            "turnover",
            "Turnover is large relative to equity.",
            "Does a lower-frequency policy survive costs?",
        )
    if drift.status is DriftStatus.DRIFTED:
        add(
            FeedbackKind.TARGET_DEVIATION,
            f"implementation gap {drift.implementation_gap:.6f}",
            "paper vs target",
            "Paper execution deviated materially from the target.",
            "Is the gap rounding, liquidity, or an accounting break?",
        )
    if abs(pnl.residual_pnl) > 1e-6 and not items:
        add(
            FeedbackKind.UNEXPLAINED,
            f"residual P&L {pnl.residual_pnl:.6f}",
            "residual",
            "The portfolio result is not fully explained.",
            "What evidence would make the residual identifiable?",
        )
    if not items:
        add(
            FeedbackKind.INSUFFICIENT_EVIDENCE,
            "no diagnostic threshold crossed",
            "none",
            "The observation does not establish why P&L occurred.",
            "What additional PIT evidence would support a claim?",
        )
    del concentration
    return items
