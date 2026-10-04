"""The shared permission registry is enforced again at every gateway call."""

from __future__ import annotations

from quantlab.agents.contracts import AgentMandate, AgentRole
from quantlab.ai.permissions import DENIED_CAPABILITIES, AiCapability, AiPermissions

DEFAULT_RESEARCH_CAPABILITIES = frozenset(
    {
        AiCapability.READ_MARKET_STATE,
        AiCapability.READ_RESEARCH,
        AiCapability.QUERY_FEATURES,
        AiCapability.QUERY_FACTORS,
        AiCapability.QUERY_REGIMES,
        AiCapability.QUERY_KNOWLEDGE,
        AiCapability.RUN_BACKTEST,
        AiCapability.RUN_VALIDATION,
        AiCapability.RUN_RISK_ANALYSIS,
        AiCapability.RUN_TCA,
        AiCapability.CREATE_MEMO,
        AiCapability.CREATE_CRITIQUE,
    }
)


def allows(mandate: AgentMandate, capability: AiCapability) -> bool:
    return capability not in DENIED_CAPABILITIES and AiPermissions(granted=mandate.granted).allows(
        capability
    )


def mandate_for(role: AgentRole, *, created_at: object) -> AgentMandate:
    return AgentMandate.model_validate(
        {
            "created_at": created_at,
            "role": role,
            "mandate": (
                "Seek long-side evidence and actively falsify the thesis."
                if role is AgentRole.BULL
                else "Independently investigate downside, squeeze risk, avoidance, and exits."
            ),
            "granted": DEFAULT_RESEARCH_CAPABILITIES,
        }
    )
