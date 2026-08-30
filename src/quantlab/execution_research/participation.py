"""Participation: filled / available volume. Caps are hard."""

from __future__ import annotations


def max_fillable(available_volume: float | None, max_participation: float) -> float | None:
    if available_volume is None:
        return None
    if available_volume < 0:
        return 0.0
    return float(available_volume) * max(0.0, min(float(max_participation), 1.0))


def participation(filled: float, available_volume: float | None) -> float | None:
    if available_volume is None or available_volume <= 0:
        return None
    return float(filled) / float(available_volume)
