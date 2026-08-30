"""Drawdown episodes. max_drawdown remains a scalar; this is the path analysis."""

from __future__ import annotations

from pydantic import BaseModel


class DrawdownEpisode(BaseModel):
    peak_index: int
    trough_index: int
    recovery_index: int | None
    peak_equity: float
    trough_equity: float
    drawdown: float
    duration: int
    recovery_duration: int | None


def drawdown_series(equity: list[float]) -> list[float]:
    peak = 0.0
    out: list[float] = []
    for value in equity:
        peak = max(peak, value)
        if peak > 0:
            out.append(value / peak - 1.0)
        else:
            out.append(0.0)
    return out


def average_drawdown(equity: list[float]) -> float:
    series = [d for d in drawdown_series(equity) if d < 0]
    if not series:
        return 0.0
    return float(sum(series) / len(series))


def episodes(equity: list[float]) -> list[DrawdownEpisode]:
    if len(equity) < 2:
        return []
    found: list[DrawdownEpisode] = []
    peak_i = 0
    peak_v = equity[0]
    trough_i = 0
    trough_v = equity[0]
    in_dd = False
    for i, value in enumerate(equity):
        if value >= peak_v:
            if in_dd and trough_v < peak_v:
                found.append(
                    DrawdownEpisode(
                        peak_index=peak_i,
                        trough_index=trough_i,
                        recovery_index=i,
                        peak_equity=peak_v,
                        trough_equity=trough_v,
                        drawdown=trough_v / peak_v - 1.0 if peak_v > 0 else 0.0,
                        duration=trough_i - peak_i,
                        recovery_duration=i - trough_i,
                    )
                )
            peak_i, peak_v = i, value
            trough_i, trough_v = i, value
            in_dd = False
            continue
        in_dd = True
        if value < trough_v:
            trough_i, trough_v = i, value
    if in_dd and trough_v < peak_v:
        found.append(
            DrawdownEpisode(
                peak_index=peak_i,
                trough_index=trough_i,
                recovery_index=None,
                peak_equity=peak_v,
                trough_equity=trough_v,
                drawdown=trough_v / peak_v - 1.0 if peak_v > 0 else 0.0,
                duration=trough_i - peak_i,
                recovery_duration=None,
            )
        )
    return found


def top_drawdowns(equity: list[float], n: int = 5) -> list[DrawdownEpisode]:
    ranked = sorted(episodes(equity), key=lambda e: e.drawdown)
    return ranked[: max(n, 0)]
