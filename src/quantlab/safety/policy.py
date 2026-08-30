"""Immutable safety policy identity. Runtime mutation is not silent."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from quantlab.data.fabric.checksums import sha256_bytes


class SafetyPolicy(BaseModel):
    model_config = ConfigDict(frozen=True)

    policy_id: str = "safety-policy-v1"
    live_trading: bool = False
    live_release_kill_default: bool = True
    max_age_ms: float = 300_000.0
    require_human_for_arm: bool = True
    note: str = "Policy hash is part of authorization identity."

    def policy_hash(self) -> str:
        return sha256_bytes(self.model_dump_json().encode())


POLICY = SafetyPolicy()
