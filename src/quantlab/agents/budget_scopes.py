"""Host-owned, stable provider-budget groupings; never derive these from model output."""

from __future__ import annotations

import re

DESK_RESEARCH_FAMILY = "desk:research"
DESKTOP_OPERATIONS_FAMILY = "desktop:operations"
RESEARCH_CHAT_FAMILY = "research:conceptual-chat"


def strategy_research_family(instrument: str) -> str:
    """Group batches for a validated exchange symbol, across bar intervals."""
    if len(instrument) > 80 or re.fullmatch(r"(?:NSE|BSE):[A-Z0-9_.-]+", instrument) is None:
        raise ValueError("INVALID_STRATEGY_BUDGET_INSTRUMENT")
    return "strategy:" + instrument
