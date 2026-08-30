"""PIT state normalization. Expanding/rolling windows end at T."""

from __future__ import annotations

from collections.abc import Sequence


def expanding_zscore(values: list[float | None], min_obs: int = 8) -> list[float | None]:
    out: list[float | None] = []
    hist: list[float] = []
    for value in values:
        if value is None:
            out.append(None)
            continue
        hist.append(value)
        if len(hist) < min_obs:
            out.append(None)
            continue
        mean = sum(hist) / len(hist)
        var = sum((x - mean) ** 2 for x in hist) / len(hist)
        out.append(0.0 if var <= 0 else (value - mean) / (var**0.5))
    return out


def rolling_zscore(
    values: list[float | None],
    window: int = 20,
    min_obs: int = 8,
) -> list[float | None]:
    out: list[float | None] = []
    hist: list[float] = []
    for value in values:
        if value is None:
            out.append(None)
            continue
        hist.append(value)
        chunk = hist[-window:]
        if len(chunk) < min_obs:
            out.append(None)
            continue
        mean = sum(chunk) / len(chunk)
        var = sum((x - mean) ** 2 for x in chunk) / len(chunk)
        out.append(0.0 if var <= 0 else (value - mean) / (var**0.5))
    return out


def expanding_tercile(values: list[float | None], min_obs: int = 8) -> list[str | None]:
    out: list[str | None] = []
    hist: list[float] = []
    for value in values:
        if value is None:
            out.append(None)
            continue
        hist.append(value)
        if len(hist) < min_obs:
            out.append(None)
            continue
        ordered = sorted(hist)
        n = len(ordered)
        lo = ordered[max(n // 3 - 1, 0)]
        hi = ordered[max((2 * n) // 3 - 1, 0)]
        if value <= lo:
            out.append("low")
        elif value <= hi:
            out.append("normal")
        else:
            out.append("high")
    return out


def series_of(snapshots: Sequence[object], field: str) -> list[float | None]:
    out: list[float | None] = []
    for item in snapshots:
        raw = getattr(item, field, None)
        if raw is None and hasattr(item, "vector"):
            raw = item.vector().get(field)
        out.append(None if raw is None else float(raw))
    return out
