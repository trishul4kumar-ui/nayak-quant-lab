"""Durable persistence for level artifacts through the existing control plane."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from quantlab.agents.adjudication_contracts import AdjudicationDecision
from quantlab.agents.adjudication_service import verify_adjudication
from quantlab.agents.repository import AgentRepository
from quantlab.trade_levels.engine import compute_trade_level_plan, default_trade_level_policy
from quantlab.trade_levels.models import ExitPolicy, TradeLevelInput, TradeLevelPlan


class TradeLevelRepository:
    """A narrow facade; it intentionally exposes no execution or sizing methods."""

    def __init__(self, path: Path | None = None) -> None:
        self._artifacts = AgentRepository(path)

    def compute(self, value: TradeLevelInput, *, now: datetime) -> TradeLevelPlan:
        decision = self._artifacts.get(value.adjudication_hash, AdjudicationDecision)
        verify_adjudication(self._artifacts, decision)
        if decision.no_trade or decision.outcome.value != value.adjudication_outcome:
            raise ValueError("adjudication is not eligible for a level plan")
        if decision.snapshot_hash != value.snapshot_hash:
            raise ValueError("level input snapshot does not match adjudication")
        policy = self._artifacts.put(default_trade_level_policy())
        frozen_input = self._artifacts.put(value)
        plan, exit_policy = compute_trade_level_plan(frozen_input, policy)
        if exit_policy is not None:
            self._artifacts.put(exit_policy)
        plan = self._artifacts.put(plan)
        self._artifacts.audit(
            "TRADE_LEVEL_PLAN_FROZEN",
            run_id=plan.plan_id,
            now=now,
            artifact_hash=plan.content_hash,
            safe_code=plan.status.value,
        )
        return plan

    def get(self, plan_hash: str) -> TradeLevelPlan:
        return self._artifacts.get(plan_hash, TradeLevelPlan)

    def list(self) -> tuple[TradeLevelPlan, ...]:
        return self._artifacts.list(TradeLevelPlan)

    def exit_policy(self, plan: TradeLevelPlan) -> ExitPolicy | None:
        if plan.exit_policy_hash is None:
            return None
        return self._artifacts.get(plan.exit_policy_hash, ExitPolicy)

    def close(self) -> None:
        self._artifacts.close()
