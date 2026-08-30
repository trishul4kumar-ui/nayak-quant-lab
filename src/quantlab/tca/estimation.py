"""Statistical estimation helpers. Inadequate samples stay NOT_TESTED."""

from __future__ import annotations


def mean_with_count(samples: list[float]) -> tuple[float | None, int]:
    if len(samples) < 8:
        return None, len(samples)
    return sum(samples) / len(samples), len(samples)
