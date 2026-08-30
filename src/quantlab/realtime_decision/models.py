"""Real-time decision types. TargetPortfolio is terminal. Not an order."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from quantlab.capital.definitions import TargetPortfolio


class CertificationStatus(StrEnum):
    UNKNOWN = "unknown"
    RESEARCH_ONLY = "research_only"
    UNCERTIFIED = "uncertified"
    CERTIFIED = "certified"
    EXPIRED = "expired"
    REVOKED = "revoked"


class ActorKind(StrEnum):
    HUMAN = "human"
    SYSTEM = "system"
    AI_SUGGESTION = "ai_suggestion"


class AbstentionReason(StrEnum):
    NONE = "none"
    STALE_DATA = "stale_data"
    MISSING_FEATURE = "missing_feature"
    INVALID_STATE = "invalid_state"
    UNAVAILABLE_MODEL = "unavailable_model"
    EXPIRED_CERT = "expired_cert"
    UNCERTIFIED_RELEASE = "uncertified_release"
    RISK_BREACH = "risk_breach"
    INFEASIBLE_PORTFOLIO = "infeasible_portfolio"
    INSUFFICIENT_LIQUIDITY = "insufficient_liquidity"
    TCA_FAILURE = "tca_failure"
    CLOCK_FAILURE = "clock_failure"
    SESSION_UNCERTAINTY = "session_uncertainty"
    SAFETY_BLOCK = "safety_block"
    AI_ACTOR = "ai_actor"


class StrategyRelease(BaseModel):
    model_config = ConfigDict(frozen=True)

    release_id: str
    strategy_id: str
    version: str
    feature_manifest_hash: str
    model_manifest_hash: str
    portfolio_manifest_hash: str
    capital_manifest_hash: str
    certification_id: str = ""
    certification_status: CertificationStatus = CertificationStatus.UNCERTIFIED
    release_hash: str
    effective_at: datetime
    expiry_at: datetime | None = None
    live_trading: bool = False
    note: str = "Never load an implicit latest release."


class RealTimeDecision(BaseModel):
    model_config = ConfigDict(frozen=True)

    decision_id: str
    decision_hash: str
    snapshot_id: str
    snapshot_hash: str
    release_id: str
    release_hash: str
    state: str
    as_of: datetime
    target: TargetPortfolio | None = None
    abstention: AbstentionReason = AbstentionReason.NONE
    cycle: tuple[str, ...] = ()
    extras: dict[str, Any] = Field(default_factory=dict)
    live_trading: bool = False
    note: str = "DECISION ≠ ORDER. TargetPortfolio is not an order intent."


def default_uncertified_release(*, as_of: datetime) -> StrategyRelease:
    return StrategyRelease(
        release_id="rel-uncertified-default",
        strategy_id="research-only",
        version="0",
        feature_manifest_hash="feat-none",
        model_manifest_hash="model-none",
        portfolio_manifest_hash="port-none",
        capital_manifest_hash="cap-none",
        certification_id="",
        certification_status=CertificationStatus.UNCERTIFIED,
        release_hash="uncertified",
        effective_at=as_of,
        expiry_at=None,
        live_trading=False,
    )


def synthetic_research_release(*, as_of: datetime) -> StrategyRelease:
    return StrategyRelease(
        release_id="rel-synthetic-research",
        strategy_id="synthetic-equal-weight",
        version="3.1.0",
        feature_manifest_hash="feat-synthetic-v1",
        model_manifest_hash="model-synthetic-v1",
        portfolio_manifest_hash="port-synthetic-v1",
        capital_manifest_hash="cap-synthetic-v1",
        certification_id="cert-research-only",
        certification_status=CertificationStatus.RESEARCH_ONLY,
        release_hash="synthetic-research-hash",
        effective_at=as_of,
        expiry_at=None,
        live_trading=False,
        note="Research-only synthetic release. Not live. Not certified for trading.",
    )
