from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from quantlab.agents.contracts import EvidenceMetric
from quantlab.agents.hashing import Artifact
from quantlab.ai.permissions import AiCapability


class ToolName(StrEnum):
    FREEZE_SNAPSHOT = "freeze_snapshot"
    INSPECT_MARKET = "inspect_market"
    QUERY_FEATURE = "query_feature"
    QUERY_KNOWLEDGE = "query_knowledge"
    QUERY_FACTOR = "query_factor"
    QUERY_REGIME = "query_regime"
    RUN_BACKTEST = "run_backtest"
    RUN_VALIDATION = "run_validation"
    RUN_ECONOMETRICS = "run_econometrics"
    RUN_MODEL_EVALUATION = "run_model_evaluation"
    RUN_ENSEMBLE_EVALUATION = "run_ensemble_evaluation"
    RUN_PORTFOLIO_SIMULATION = "run_portfolio_simulation"
    RUN_RISK_ANALYSIS = "run_risk_analysis"
    RUN_TCA = "run_tca"


TOOL_CAPABILITIES = {
    ToolName.FREEZE_SNAPSHOT: AiCapability.READ_MARKET_STATE,
    ToolName.INSPECT_MARKET: AiCapability.READ_MARKET_STATE,
    ToolName.QUERY_FEATURE: AiCapability.QUERY_FEATURES,
    ToolName.QUERY_KNOWLEDGE: AiCapability.QUERY_KNOWLEDGE,
    ToolName.QUERY_FACTOR: AiCapability.QUERY_FACTORS,
    ToolName.QUERY_REGIME: AiCapability.QUERY_REGIMES,
    ToolName.RUN_BACKTEST: AiCapability.RUN_BACKTEST,
    ToolName.RUN_VALIDATION: AiCapability.RUN_VALIDATION,
    ToolName.RUN_ECONOMETRICS: AiCapability.RUN_ECONOMETRICS,
    ToolName.RUN_MODEL_EVALUATION: AiCapability.RUN_MODEL_EVALUATION,
    ToolName.RUN_ENSEMBLE_EVALUATION: AiCapability.RUN_ENSEMBLE_EVALUATION,
    ToolName.RUN_PORTFOLIO_SIMULATION: AiCapability.RUN_PORTFOLIO_SIMULATION,
    ToolName.RUN_RISK_ANALYSIS: AiCapability.RUN_RISK_ANALYSIS,
    ToolName.RUN_TCA: AiCapability.RUN_TCA,
}


class ToolArguments(Artifact):
    security_id: str | None = None
    analysis_id: str | None = None
    lookback: int = Field(default=20, ge=2, le=252)


class AgentToolRequest(Artifact):
    request_id: str
    run_id: str
    context_hash: str
    snapshot_hash: str
    tool: ToolName
    arguments: ToolArguments


class AgentToolResult(Artifact):
    request_hash: str
    run_id: str
    context_hash: str
    snapshot_hash: str
    tool: ToolName
    status: str
    metrics: tuple[EvidenceMetric, ...] = ()
    error_code: str | None = None
