"""Drawdown episodes from an equity path. Single points do not invent recovery."""

from __future__ import annotations

from datetime import datetime

from quantlab.monitoring.models import DrawdownEpisode, EquityPoint, RiskObservation


def drawdown_from_path(path: list[EquityPoint]) -> RiskObservation:
    if not path:
        return RiskObservation(note="No equity path.")
    peak = path[0].equity
    peak_time = path[0].as_of
    trough = path[0].equity
    trough_time = path[0].as_of
    max_dd = 0.0
    episodes: list[DrawdownEpisode] = []
    in_dd = False
    ep_peak = peak
    ep_peak_t = peak_time
    for point in path:
        if point.equity > peak:
            if in_dd:
                episodes.append(
                    DrawdownEpisode(
                        peak_equity=ep_peak,
                        trough_equity=trough,
                        drawdown=(trough / ep_peak - 1.0) if ep_peak else 0.0,
                        start=ep_peak_t,
                        trough=trough_time,
                        recovered=point.as_of,
                    )
                )
                in_dd = False
            peak = point.equity
            peak_time = point.as_of
            trough = point.equity
            trough_time = point.as_of
            ep_peak = peak
            ep_peak_t = peak_time
        if point.equity < trough:
            trough = point.equity
            trough_time = point.as_of
        dd = (point.equity / peak - 1.0) if peak else 0.0
        if dd < 0:
            in_dd = True
            ep_peak = peak
            ep_peak_t = peak_time
        if dd < max_dd:
            max_dd = dd
    if in_dd and peak:
        episodes.append(
            DrawdownEpisode(
                peak_equity=ep_peak,
                trough_equity=trough,
                drawdown=(trough / ep_peak - 1.0) if ep_peak else 0.0,
                start=ep_peak_t,
                trough=trough_time,
                recovered=None,
            )
        )
    current = (path[-1].equity / peak - 1.0) if peak else 0.0
    vol = None
    if len(path) >= 3:
        rets: list[float] = []
        for i in range(1, len(path)):
            prev = path[i - 1].equity
            if prev:
                rets.append(path[i].equity / prev - 1.0)
        if len(rets) >= 2:
            mean = sum(rets) / len(rets)
            var = sum((r - mean) ** 2 for r in rets) / (len(rets) - 1)
            vol = var**0.5
    return RiskObservation(
        current_drawdown=min(current, 0.0),
        max_drawdown=max_dd,
        rolling_volatility=vol,
        episodes=episodes,
        note="Drawdown is diagnostic. Limits are not changed.",
    )


def recovery_time(episode: DrawdownEpisode) -> datetime | None:
    return episode.recovered
