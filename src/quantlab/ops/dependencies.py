"""Dependency checks. Unexpected or missing dependencies fail closed."""

from __future__ import annotations

EXPECTED = frozenset(
    {
        "ledger",
        "catalog",
        "health",
        "safety",
        "shadow",
        "paper_oms",
    }
)


def validate(observed: set[str]) -> tuple[str, ...]:
    unexpected = tuple(sorted(observed - EXPECTED))
    missing = tuple(sorted(EXPECTED - observed))
    return unexpected + missing
