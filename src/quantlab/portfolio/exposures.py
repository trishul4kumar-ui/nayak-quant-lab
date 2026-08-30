"""Gross, net, concentration. Beta/sector/factor stay NOT_TESTED without PIT data."""

from __future__ import annotations

from pydantic import BaseModel

from quantlab.domain.research import CheckResult


class ExposureReport(BaseModel):
    schema_version: str = "1"
    n_positions: int = 0
    gross: float = 0.0
    net: float = 0.0
    cash: float = 0.0
    max_weight: float = 0.0
    top5_weight: float = 0.0
    top10_weight: float = 0.0
    hhi: float | None = None
    effective_n: float | None = None
    beta: CheckResult = CheckResult.NOT_TESTED
    sector: CheckResult = CheckResult.NOT_TESTED
    factor: CheckResult = CheckResult.NOT_TESTED
    liquidity: CheckResult = CheckResult.NOT_TESTED
    capacity: CheckResult = CheckResult.NOT_TESTED
    benchmark: str = "NOT_AVAILABLE"
    note: str = "beta/sector/cap/ADV/benchmark are NOT_TESTED until PIT series exist"


def exposure_report(weights: dict[str, float]) -> ExposureReport:
    held = {k: v for k, v in weights.items() if abs(v) > 1e-12}
    gross = sum(abs(v) for v in held.values())
    net = sum(held.values())
    abs_w = sorted((abs(v) for v in held.values()), reverse=True)
    if gross <= 0:
        return ExposureReport(n_positions=0, cash=1.0)
    shares = [w / gross for w in abs_w]
    hhi = sum(s * s for s in shares)
    return ExposureReport(
        n_positions=len(held),
        gross=gross,
        net=net,
        cash=1.0 - net,
        max_weight=abs_w[0] if abs_w else 0.0,
        top5_weight=sum(abs_w[:5]),
        top10_weight=sum(abs_w[:10]),
        hhi=hhi,
        effective_n=None if hhi <= 0 else 1.0 / hhi,
    )
