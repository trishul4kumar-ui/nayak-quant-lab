"""Feature specifications. Lookback is trading sessions, not calendar days."""

from __future__ import annotations

from pydantic import BaseModel

from quantlab.data.fabric.types import FeatureStatus


class FeatureSpec(BaseModel):
    name: str
    lookback_sessions: int
    calendar_version: str
    version: str = "1"
    description: str = ""

    def status(self, available_sessions: int) -> FeatureStatus:
        if available_sessions < 0:
            return FeatureStatus.INVALID
        if available_sessions < self.lookback_sessions + 1:
            return FeatureStatus.INSUFFICIENT_HISTORY
        return FeatureStatus.READY


def momentum_spec(lookback_sessions: int, calendar_version: str) -> FeatureSpec:
    return FeatureSpec(
        name=f"momentum_{lookback_sessions}",
        lookback_sessions=lookback_sessions,
        calendar_version=calendar_version,
        version="1",
        description="close[t]/close[t-N]-1 over N trading sessions on the research calendar",
    )
