"""Factor attribution architecture. No factor library is bundled."""

from __future__ import annotations

from pydantic import BaseModel, Field

from quantlab.domain.research import CheckResult


class FactorExposure(BaseModel):
    name: str
    value: float | None = None
    status: CheckResult = CheckResult.NOT_TESTED
    note: str = ""


class AttributionReport(BaseModel):
    schema_version: str = "1"
    status: CheckResult = CheckResult.NOT_TESTED
    exposures: list[FactorExposure] = Field(default_factory=list)
    note: str = "market/size/value/momentum/vol/quality/sector factors are not ingested"


def empty_attribution() -> AttributionReport:
    names = ("market_beta", "size", "value", "momentum", "volatility", "quality", "sector")
    return AttributionReport(
        exposures=[FactorExposure(name=name) for name in names],
    )
