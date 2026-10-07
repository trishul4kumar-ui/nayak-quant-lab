"""Durable packet/event storage via the existing append-only control plane."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Literal

from quantlab.agents.repository import AgentRepository
from quantlab.trade_candidates.lifecycle import ensure_transition
from quantlab.trade_candidates.models import (
    CandidateLifecycleEvent,
    CandidateStatus,
    TradeCandidatePacket,
)


class CandidateRepository:
    def __init__(self, path: Path | None = None) -> None:
        self._artifacts = AgentRepository(path)

    def put(self, candidate: TradeCandidatePacket) -> TradeCandidatePacket:
        for existing in self._artifacts.list(TradeCandidatePacket):
            if (
                existing.candidate_id == candidate.candidate_id
                and existing.content_hash != candidate.content_hash
            ):
                raise ValueError("candidate identity cannot be silently overwritten")
        return self._artifacts.put(candidate)

    def transition(
        self,
        candidate: TradeCandidatePacket,
        target: CandidateStatus,
        *,
        now: datetime,
        reason: str,
        actor: Literal["SYSTEM", "HUMAN"] = "SYSTEM",
    ) -> CandidateLifecycleEvent:
        ensure_transition(candidate.status, target)
        if (
            target in {CandidateStatus.PAPER_ELIGIBLE, CandidateStatus.SHADOW_ELIGIBLE}
            and candidate.hard_blockers
        ):
            raise ValueError("blocked candidate cannot become paper/shadow eligible")
        event = CandidateLifecycleEvent(
            created_at=now,
            schema_version="trade-candidates-v1",
            candidate_hash=candidate.candidate_hash,
            from_status=candidate.status,
            to_status=target,
            reason=reason,
            actor=actor,
        )
        return self._artifacts.put(event)

    def list(self) -> tuple[TradeCandidatePacket, ...]:
        return self._artifacts.list(TradeCandidatePacket)

    def close(self) -> None:
        self._artifacts.close()
