"""Equal-weight universe market returns and rolling betas. Not NIFTY."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from quantlab.core.errors import FactorError
from quantlab.core.identifiers import InstrumentId
from quantlab.domain.models import OHLCVBar
from quantlab.domain.research import CheckResult
from quantlab.features.engine import Panel, pit_bars, session_calendar


class BetaReport(BaseModel):
    schema_version: str = "1"
    benchmark: str = "equal_weight_universe"
    lookback: int = 20
    as_of: datetime | None = None
    betas: dict[str, float] = Field(default_factory=dict)
    market_return: float | None = None
    mean: float | None = None
    std: float | None = None
    minimum: float | None = None
    maximum: float | None = None
    status: CheckResult = CheckResult.NOT_TESTED
    note: str = "beta vs equal-weight Universe(T); not an official index"


def equal_weight_market_returns(
    bars: dict[InstrumentId, list[OHLCVBar]],
    dates: list[datetime] | None = None,
) -> dict[datetime, float]:
    """CS mean of simple close-to-close returns among names with PIT history."""
    calendar = dates or session_calendar(bars)
    out: dict[datetime, float] = {}
    for i in range(1, len(calendar)):
        prev, as_of = calendar[i - 1], calendar[i]
        rets: list[float] = []
        for series in bars.values():
            available = pit_bars(series, as_of)
            by_event = {b.pit.event_time: b.close for b in available}
            p0, p1 = by_event.get(prev), by_event.get(as_of)
            if p0 and p1 and p0 > 0:
                rets.append(p1 / p0 - 1.0)
        if len(rets) >= 2:
            out[as_of] = sum(rets) / len(rets)
    return out


def rolling_betas(
    bars: dict[InstrumentId, list[OHLCVBar]],
    as_of: datetime,
    lookback: int = 20,
    min_obs: int = 10,
) -> BetaReport:
    if lookback < 2:
        raise FactorError("beta lookback must be >= 2")
    dates = [d for d in session_calendar(bars) if d <= as_of]
    market = equal_weight_market_returns(bars, dates)
    m_dates = [d for d in dates if d in market]
    if len(m_dates) < min_obs:
        return BetaReport(
            lookback=lookback,
            as_of=as_of,
            status=CheckResult.NOT_TESTED,
            note="insufficient PIT market observations for equal-weight beta",
        )
    window = m_dates[-lookback:]
    m_vals = [market[d] for d in window]
    var_m = _var(m_vals)
    if var_m <= 0:
        raise FactorError("market return variance is zero; beta undefined")
    betas: dict[str, float] = {}
    for inst, series in bars.items():
        available = pit_bars(series, as_of)
        prices = {b.pit.event_time: b.close for b in available}
        r_i: list[float] = []
        aligned_m: list[float] = []
        for day in window:
            idx = dates.index(day)
            if idx == 0:
                continue
            prev = dates[idx - 1]
            p0, p1 = prices.get(prev), prices.get(day)
            if p0 and p1 and p0 > 0:
                r_i.append(p1 / p0 - 1.0)
                aligned_m.append(market[day])
        if len(r_i) < min_obs:
            continue
        betas[str(inst)] = _cov(r_i, aligned_m) / var_m
    if not betas:
        return BetaReport(lookback=lookback, as_of=as_of, status=CheckResult.NOT_TESTED)
    values = list(betas.values())
    return BetaReport(
        lookback=lookback,
        as_of=as_of,
        betas=betas,
        market_return=market.get(as_of),
        mean=sum(values) / len(values),
        std=_std(values),
        minimum=min(values),
        maximum=max(values),
        status=CheckResult.PASS,
        note="PIT equal-weight universe beta; not NIFTY",
    )


def beta_panel(
    bars: dict[InstrumentId, list[OHLCVBar]],
    dates: list[datetime],
    lookback: int = 20,
) -> Panel:
    panel: Panel = {}
    for as_of in dates:
        report = rolling_betas(bars, as_of, lookback=lookback)
        if report.betas:
            panel[as_of] = dict(report.betas)
    return panel


def _var(xs: list[float]) -> float:
    if len(xs) < 2:
        return 0.0
    mean = sum(xs) / len(xs)
    return sum((x - mean) ** 2 for x in xs) / len(xs)


def _std(xs: list[float]) -> float:
    return float(_var(xs) ** 0.5)


def _cov(xs: list[float], ys: list[float]) -> float:
    n = min(len(xs), len(ys))
    if n < 2:
        return 0.0
    mx = sum(xs[:n]) / n
    my = sum(ys[:n]) / n
    return sum((xs[i] - mx) * (ys[i] - my) for i in range(n)) / n


def cross_sectional_dispersion(
    bars: dict[InstrumentId, list[OHLCVBar]],
    as_of: datetime,
) -> float | None:
    """Std of PIT simple returns across names present at as_of. Not a forecast."""
    dates = [d for d in session_calendar(bars) if d <= as_of]
    if len(dates) < 2:
        return None
    prev, day = dates[-2], dates[-1]
    rets: list[float] = []
    for series in bars.values():
        available = pit_bars(series, as_of)
        prices = {b.pit.event_time: b.close for b in available}
        p0, p1 = prices.get(prev), prices.get(day)
        if p0 and p1 and p0 > 0:
            rets.append(p1 / p0 - 1.0)
    if len(rets) < 2:
        return None
    return _std(rets)
