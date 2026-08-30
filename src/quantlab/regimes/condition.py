"""Regime-conditional slices of existing alpha / factor / risk objects."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from quantlab.alpha.ic import FeatureICReport, information_coefficient
from quantlab.core.errors import CovarianceError
from quantlab.core.identifiers import InstrumentId
from quantlab.domain.models import OHLCVBar
from quantlab.domain.research import CheckResult
from quantlab.features.engine import Panel
from quantlab.portfolio.covariance import CovarianceReport, estimate_covariance
from quantlab.regimes.detectors import RegimeObservation


class ConditionalSlice(BaseModel):
    schema_version: str = "1"
    regime: str
    n: int = 0
    ic: FeatureICReport | None = None
    covariance: CovarianceReport | None = None
    status: CheckResult = CheckResult.PASS
    note: str = "Association given a contemporaneous regime label; not causal and not alpha"


def dates_for(observations: list[RegimeObservation], regime: str) -> list[datetime]:
    return [row.as_of for row in observations if row.hard_label == regime]


def conditional_ic(
    feature: Panel,
    label: Panel,
    observations: list[RegimeObservation],
    regime: str,
    min_sample: int = 8,
) -> ConditionalSlice:
    keep = set(dates_for(observations, regime))
    sub_f = {d: row for d, row in feature.items() if d in keep}
    sub_l = {d: row for d, row in label.items() if d in keep}
    ic = information_coefficient(sub_f, sub_l, min_sample=min_sample)
    status = ic.status if ic.n else CheckResult.NOT_TESTED
    return ConditionalSlice(
        regime=regime,
        n=ic.n,
        ic=ic,
        status=status,
        note="IC inside one contemporaneous regime; synthetic IC is not market evidence",
    )


def conditional_covariance(
    bars: dict[InstrumentId, list[OHLCVBar]],
    observations: list[RegimeObservation],
    regime: str,
    names: list[str],
    lookback: int = 20,
) -> ConditionalSlice:
    dates = dates_for(observations, regime)
    if len(dates) < lookback:
        return ConditionalSlice(
            regime=regime,
            n=len(dates),
            status=CheckResult.NOT_TESTED,
            note=f"need lookback={lookback} sessions in regime; have {len(dates)}",
        )
    as_of = dates[-1]
    try:
        cov = estimate_covariance(bars, as_of, names, lookback)
    except CovarianceError as exc:
        return ConditionalSlice(
            regime=regime,
            n=len(dates),
            status=CheckResult.NOT_TESTED,
            note=str(exc),
        )
    return ConditionalSlice(regime=regime, n=len(dates), covariance=cov, status=CheckResult.PASS)
