from enum import StrEnum

from pydantic import BaseModel, Field


class AiCapability(StrEnum):
    READ_MARKET_DATA = "READ_MARKET_DATA"
    READ_RESEARCH = "READ_RESEARCH"
    CREATE_HYPOTHESIS = "CREATE_HYPOTHESIS"
    CREATE_FEATURE = "CREATE_FEATURE"
    CREATE_SIGNAL = "CREATE_SIGNAL"
    RUN_EXPERIMENT = "RUN_EXPERIMENT"
    RUN_BACKTEST = "RUN_BACKTEST"
    CREATE_MODEL = "CREATE_MODEL"
    REQUEST_PAPER_ORDER = "REQUEST_PAPER_ORDER"
    REQUEST_LIVE_ORDER = "REQUEST_LIVE_ORDER"
    OVERRIDE_RESEARCH_GATE = "OVERRIDE_RESEARCH_GATE"


class AiPermissions(BaseModel):
    """Agents never receive REQUEST_LIVE_ORDER or OVERRIDE_RESEARCH_GATE."""

    granted: frozenset[AiCapability] = Field(
        default_factory=lambda: frozenset(
            {
                AiCapability.READ_MARKET_DATA,
                AiCapability.READ_RESEARCH,
                AiCapability.CREATE_HYPOTHESIS,
                AiCapability.CREATE_FEATURE,
                AiCapability.CREATE_SIGNAL,
                AiCapability.RUN_EXPERIMENT,
                AiCapability.RUN_BACKTEST,
            }
        )
    )

    def allows(self, capability: AiCapability) -> bool:
        if capability in {AiCapability.REQUEST_LIVE_ORDER, AiCapability.OVERRIDE_RESEARCH_GATE}:
            return False
        return capability in self.granted
