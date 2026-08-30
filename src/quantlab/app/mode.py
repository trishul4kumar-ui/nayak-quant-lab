"""Operating modes. LIVE is never implied by the UI alone."""

from __future__ import annotations

from enum import StrEnum

from quantlab.core.config import LiveSafetyGates


class AppMode(StrEnum):
    DEVELOPMENT = "development"
    RESEARCH = "research"
    PAPER = "paper"
    SHADOW = "shadow"
    LIVE = "live"


def resolve_mode(requested: str, gates: LiveSafetyGates) -> AppMode:
    """LIVE requires every safety gate. Otherwise fail closed to RESEARCH."""
    try:
        mode = AppMode(requested.strip().lower())
    except ValueError:
        return AppMode.RESEARCH
    if mode is AppMode.LIVE and not gates.all_pass():
        return AppMode.RESEARCH
    return mode
