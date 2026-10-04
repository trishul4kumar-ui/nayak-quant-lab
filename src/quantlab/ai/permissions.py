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
    READ_MARKET_STATE = "READ_MARKET_STATE"
    READ_BROKER_OBSERVATION = "READ_BROKER_OBSERVATION"
    QUERY_KNOWLEDGE = "QUERY_KNOWLEDGE"
    QUERY_FEATURES = "QUERY_FEATURES"
    QUERY_FACTORS = "QUERY_FACTORS"
    QUERY_REGIMES = "QUERY_REGIMES"
    RUN_VALIDATION = "RUN_VALIDATION"
    RUN_ECONOMETRICS = "RUN_ECONOMETRICS"
    RUN_MODEL_EVALUATION = "RUN_MODEL_EVALUATION"
    RUN_ENSEMBLE_EVALUATION = "RUN_ENSEMBLE_EVALUATION"
    RUN_PORTFOLIO_SIMULATION = "RUN_PORTFOLIO_SIMULATION"
    RUN_RISK_ANALYSIS = "RUN_RISK_ANALYSIS"
    RUN_TCA = "RUN_TCA"
    CREATE_MEMO = "CREATE_MEMO"
    CREATE_CRITIQUE = "CREATE_CRITIQUE"
    REQUEST_PAPER_ACTION = "REQUEST_PAPER_ACTION"
    PLACE_LIVE_ORDER = "PLACE_LIVE_ORDER"
    MODIFY_LIVE_ORDER = "MODIFY_LIVE_ORDER"
    CANCEL_LIVE_ORDER = "CANCEL_LIVE_ORDER"
    OVERRIDE_RISK = "OVERRIDE_RISK"
    CERTIFY_RELEASE = "CERTIFY_RELEASE"
    AUTHORIZE_EXECUTION = "AUTHORIZE_EXECUTION"
    CLEAR_KILL_SWITCH = "CLEAR_KILL_SWITCH"
    EDIT_OWN_PERMISSIONS = "EDIT_OWN_PERMISSIONS"
    READ_SECRETS = "READ_SECRETS"
    EXECUTE_ARBITRARY_CODE = "EXECUTE_ARBITRARY_CODE"


# Shared by legacy chat and the new desk. Even explicitly granting these cannot allow them.
DENIED_CAPABILITIES = frozenset(
    {
        AiCapability.REQUEST_LIVE_ORDER,
        AiCapability.OVERRIDE_RESEARCH_GATE,
        AiCapability.PLACE_LIVE_ORDER,
        AiCapability.MODIFY_LIVE_ORDER,
        AiCapability.CANCEL_LIVE_ORDER,
        AiCapability.OVERRIDE_RISK,
        AiCapability.CERTIFY_RELEASE,
        AiCapability.AUTHORIZE_EXECUTION,
        AiCapability.CLEAR_KILL_SWITCH,
        AiCapability.EDIT_OWN_PERMISSIONS,
        AiCapability.READ_SECRETS,
        AiCapability.EXECUTE_ARBITRARY_CODE,
    }
)


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
        if capability in DENIED_CAPABILITIES:
            return False
        return capability in self.granted
