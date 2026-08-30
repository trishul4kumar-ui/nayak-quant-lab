"""Gate verdicts. UNKNOWN is never PASS."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class GateVerdict(StrEnum):
    PASS = "pass"
    WARN = "warn"
    BLOCK = "block"
    NOT_TESTED = "not_tested"
    EMERGENCY = "emergency"


class GateId(StrEnum):
    G0_LIVE_MODE = "G0_LIVE_MODE"
    G1_RESEARCH_INTEGRITY = "G1_RESEARCH_INTEGRITY"
    G2_CERTIFICATION = "G2_CERTIFICATION"
    G3_SHADOW_EVIDENCE = "G3_SHADOW_EVIDENCE"
    G4_MARKET_DATA = "G4_MARKET_DATA"
    G5_ACCOUNT_STATE = "G5_ACCOUNT_STATE"
    G6_RISK = "G6_RISK"
    G7_ORDER_SAFETY = "G7_ORDER_SAFETY"
    G8_STALENESS = "G8_STALENESS"
    G9_RECONCILIATION = "G9_RECONCILIATION"
    G10_KILL_SWITCH = "G10_KILL_SWITCH"
    G11_IDEMPOTENCY = "G11_IDEMPOTENCY"
    G12_HUMAN_AUTH = "G12_HUMAN_AUTH"
    G13_AI_BOUNDARY = "G13_AI_BOUNDARY"
    G14_EMERGENCY = "G14_EMERGENCY"
    G15_FINAL_RELEASE = "G15_FINAL_RELEASE"


class GateResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    gate_id: GateId
    verdict: GateVerdict
    reason: str
    critical: bool = True

    @property
    def blocks_release(self) -> bool:
        if self.verdict in {GateVerdict.BLOCK, GateVerdict.EMERGENCY}:
            return True
        return bool(self.critical and self.verdict is GateVerdict.NOT_TESTED)
