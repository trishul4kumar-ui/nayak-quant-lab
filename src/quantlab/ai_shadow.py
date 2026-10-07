"""Phase 52 guardrails layered on the existing production-shadow service."""

from __future__ import annotations

from dataclasses import dataclass

from quantlab.production_shadow.models import ProductionShadowRun, ShadowCheckResult


@dataclass(frozen=True)
class ShadowDeskStatus:
    labels: tuple[str, ...]
    readiness: ShadowCheckResult
    broker_writes: int = 0


def summarize_shadow(run: ProductionShadowRun) -> ShadowDeskStatus:
    """A single passing run never overrides explicit missing/failed production evidence."""
    dimensions = tuple(run.readiness.dimensions.values())
    readiness = (
        ShadowCheckResult.PASS
        if dimensions and all(value is ShadowCheckResult.PASS for value in dimensions)
        else ShadowCheckResult.NOT_TESTED
    )
    return ShadowDeskStatus(
        labels=("REAL MARKET DATA", "SHADOW ORDER", "SIMULATED FILL", "NO BROKER WRITE"),
        readiness=readiness,
        broker_writes=0,
    )
