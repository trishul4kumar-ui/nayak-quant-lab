"""Versioned research hypotheses. Distinct from domain.research.ResearchHypothesis."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from quantlab.backtest.spec import config_hash
from quantlab.orchestration.contracts import ResearchStatus
from quantlab.orchestration.errors import OrchestrationError
from quantlab.orchestration.status import transition


class HypothesisSpec(BaseModel):
    """Control-plane hypothesis. Not an alpha, feature, or portfolio."""

    hypothesis_id: str
    version: str = "1"
    title: str
    description: str
    economic_rationale: str = ""
    null_hypothesis: str = ""
    expected_direction: str = ""
    target: str = "next_bar_return"
    horizon: str = "1d"
    universe_definition: str = "synthetic_nse_cash"
    information_cutoff: str = "available_time <= decision_time"
    status: ResearchStatus = ResearchStatus.REGISTERED
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    parent_hypothesis: str = ""
    tags: list[str] = Field(default_factory=list)
    provenance: str = "orchestration_seed"
    notes: str = (
        "A registered hypothesis is not evidence. Synthetic confirmation is not market alpha."
    )

    def identity_payload(self) -> dict[str, object]:
        return {
            "hypothesis_id": self.hypothesis_id,
            "version": self.version,
            "title": self.title,
            "description": self.description,
            "economic_rationale": self.economic_rationale,
            "null_hypothesis": self.null_hypothesis,
            "expected_direction": self.expected_direction,
            "target": self.target,
            "horizon": self.horizon,
            "universe_definition": self.universe_definition,
            "information_cutoff": self.information_cutoff,
            "parent_hypothesis": self.parent_hypothesis,
            "tags": list(self.tags),
        }

    def identity_hash(self) -> str:
        return config_hash(self.identity_payload())

    def with_status(self, status: ResearchStatus) -> HypothesisSpec:
        transition(self.status, status)
        return self.model_copy(update={"status": status})


def assert_frozen(original: HypothesisSpec, current: HypothesisSpec) -> None:
    if original.identity_hash() != current.identity_hash():
        raise OrchestrationError("hypothesis identity mutated after freeze; bump version")
