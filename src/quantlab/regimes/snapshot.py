"""Cross-sectional market snapshot at T. Does not replace per-instrument MarketState."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from quantlab.core.errors import CovarianceError
from quantlab.core.identifiers import InstrumentId
from quantlab.domain.models import OHLCVBar
from quantlab.domain.research import CheckResult
from quantlab.factors.market import cross_sectional_dispersion, equal_weight_market_returns
from quantlab.features.engine import pit_bars, session_calendar
from quantlab.math.metrics import realized_vol


class StateSnapshot(BaseModel):
    """Market-level observables at decision_time. Missing is None, not zero."""

    schema_version: str = "1"
    as_of: datetime
    n_names: int = 0
    market_ew_return: float | None = None
    market_ew_return_20: float | None = None
    realized_vol_20: float | None = None
    dispersion_cs: float | None = None
    breadth_sign: float | None = None
    avg_pairwise_corr: float | None = None
    ew_drawdown: float | None = None
    vol_velocity: float | None = None
    index_nifty_return: float | None = None
    liquidity_adv: float | None = None
    missing: list[str] = Field(default_factory=list)
    status: CheckResult = CheckResult.PASS
    note: str = (
        "Equal-weight universe observables; not NIFTY. "
        "A snapshot describes state, it does not forecast."
    )

    def vector(self) -> dict[str, float | None]:
        return {
            "market_ew_return": self.market_ew_return,
            "market_ew_return_20": self.market_ew_return_20,
            "realized_vol_20": self.realized_vol_20,
            "dispersion_cs": self.dispersion_cs,
            "breadth_sign": self.breadth_sign,
            "avg_pairwise_corr": self.avg_pairwise_corr,
            "ew_drawdown": self.ew_drawdown,
            "vol_velocity": self.vol_velocity,
        }


def compute_snapshot(
    bars: dict[InstrumentId, list[OHLCVBar]],
    as_of: datetime,
    lookback: int = 20,
) -> StateSnapshot:
    dates = [d for d in session_calendar(bars) if d <= as_of]
    missing = ["index_nifty_return", "liquidity_adv"]
    ew = equal_weight_market_returns(bars, dates)
    last_ret = ew.get(as_of)
    window = [ew[d] for d in dates if d in ew][-lookback:]
    vol = realized_vol(window) if len(window) >= 2 else None
    ret20 = sum(window) if len(window) >= lookback else None
    disp = cross_sectional_dispersion(bars, as_of)
    breadth = _breadth(bars, as_of, dates)
    corr = _avg_corr(bars, as_of, lookback)
    dd = _ew_drawdown(ew, dates)
    n_names = sum(1 for series in bars.values() if pit_bars(series, as_of))
    if last_ret is None:
        missing.append("market_ew_return")
    if ret20 is None:
        missing.append("market_ew_return_20")
    if vol is None:
        missing.append("realized_vol_20")
    if disp is None:
        missing.append("dispersion_cs")
    if breadth is None:
        missing.append("breadth_sign")
    if corr is None:
        missing.append("avg_pairwise_corr")
    if dd is None:
        missing.append("ew_drawdown")
    status = CheckResult.WARN if missing else CheckResult.PASS
    return StateSnapshot(
        as_of=as_of,
        n_names=n_names,
        market_ew_return=last_ret,
        market_ew_return_20=ret20,
        realized_vol_20=vol,
        dispersion_cs=disp,
        breadth_sign=breadth,
        avg_pairwise_corr=corr,
        ew_drawdown=dd,
        missing=sorted(set(missing)),
        status=status,
    )


def compute_snapshot_panel(
    bars: dict[InstrumentId, list[OHLCVBar]],
    lookback: int = 20,
) -> list[StateSnapshot]:
    dates = session_calendar(bars)
    out: list[StateSnapshot] = []
    prev_vol: float | None = None
    for as_of in dates:
        snap = compute_snapshot(bars, as_of, lookback=lookback)
        if prev_vol is not None and snap.realized_vol_20 is not None:
            snap = snap.model_copy(update={"vol_velocity": snap.realized_vol_20 - prev_vol})
        else:
            snap = snap.model_copy(update={"missing": sorted(set(snap.missing + ["vol_velocity"]))})
        if snap.realized_vol_20 is not None:
            prev_vol = snap.realized_vol_20
        out.append(snap)
    return out


def _breadth(
    bars: dict[InstrumentId, list[OHLCVBar]],
    as_of: datetime,
    dates: list[datetime],
) -> float | None:
    if len(dates) < 2:
        return None
    prev, day = dates[-2], dates[-1]
    if day != as_of:
        prev_i = dates.index(as_of) if as_of in dates else -1
        if prev_i < 1:
            return None
        prev, day = dates[prev_i - 1], dates[prev_i]
    signs: list[float] = []
    for series in bars.values():
        available = pit_bars(series, as_of)
        prices = {b.pit.event_time: b.close for b in available}
        p0, p1 = prices.get(prev), prices.get(day)
        if p0 and p1 and p0 > 0:
            signs.append(1.0 if p1 > p0 else 0.0)
    if len(signs) < 2:
        return None
    return sum(signs) / len(signs)


def _avg_corr(
    bars: dict[InstrumentId, list[OHLCVBar]],
    as_of: datetime,
    lookback: int,
) -> float | None:
    from quantlab.portfolio.covariance import pit_return_matrix

    names = [str(inst) for inst in bars]
    try:
        _kept, arr = pit_return_matrix(bars, as_of, names, lookback)
    except CovarianceError:
        return None
    if arr.shape[1] < 3 or arr.shape[0] < 5:
        return None
    import numpy as np

    corr = np.corrcoef(arr, rowvar=False)
    if not np.isfinite(corr).all():
        return None
    n = corr.shape[0]
    off = float(corr.sum() - np.trace(corr)) / float(n * (n - 1))
    return off


def _ew_drawdown(ew: dict[datetime, float], dates: list[datetime]) -> float | None:
    wealth = 1.0
    peak = 1.0
    dd: float | None = None
    used = False
    for day in dates:
        ret = ew.get(day)
        if ret is None:
            continue
        used = True
        wealth *= 1.0 + ret
        peak = max(peak, wealth)
        if peak > 0:
            dd = wealth / peak - 1.0 if dd is None else min(dd, wealth / peak - 1.0)
    return dd if used else None
