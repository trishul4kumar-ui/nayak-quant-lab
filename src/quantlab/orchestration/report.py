"""Scientific discovery reports. FACT / MEASUREMENT / INFERENCE / NOT_TESTED stay labelled."""

from __future__ import annotations

from pydantic import BaseModel, Field

from quantlab.orchestration.ablation import AblationReport
from quantlab.orchestration.comparison import ComparisonReport
from quantlab.orchestration.contracts import ResearchQuality, ResearchStatus
from quantlab.orchestration.discovery import DiscoverySummary
from quantlab.orchestration.falsification import FalsificationReport
from quantlab.orchestration.family import DegreesOfFreedom
from quantlab.orchestration.lineage import ResearchGraph
from quantlab.orchestration.pareto import ParetoReport
from quantlab.orchestration.robustness import RobustnessReport
from quantlab.orchestration.selection import CandidateOutcome
from quantlab.orchestration.sensitivity import SensitivityReport
from quantlab.research.gate import ResearchGateResult
from quantlab.research.multiple_testing import MultipleTestingReport


class OrchestrationReport(BaseModel):
    schema_version: str = "1"
    hypothesis_id: str
    hypothesis_title: str
    experiment_id: str
    family_id: str
    dataset_id: str
    snapshot_id: str
    data_kind: str = "synthetic"
    pit_integrity: dict[str, str] = Field(default_factory=dict)
    candidate_space: str = ""
    candidates: list[CandidateOutcome] = Field(default_factory=list)
    discovery: DiscoverySummary
    comparison: ComparisonReport
    ablation: AblationReport
    falsification: FalsificationReport
    sensitivity: SensitivityReport
    robustness: RobustnessReport
    multiple_testing: MultipleTestingReport
    degrees_of_freedom: DegreesOfFreedom
    pareto: ParetoReport
    lineage: ResearchGraph
    gate: ResearchGateResult
    status: ResearchStatus = ResearchStatus.COMPLETED
    quality: ResearchQuality = ResearchQuality.EXPLORATORY
    selected_candidate: str = ""
    baseline_id: str = "equal_weight"
    execution_model_id: str = "exec_base"
    execution_cost: float | None = None
    truncated_by_budget: bool = False
    identity_hash: str = ""
    config_hash: str = ""
    not_tested: list[str] = Field(default_factory=list)
    conclusion: str = ""
    note: str = (
        "FACT: what was run. MEASUREMENT: recorded metrics. "
        "STATISTICAL INFERENCE: multiple-testing diagnostics. "
        "ASSUMPTION: synthetic universe. NOT_TESTED: remaining uncertainty. "
        "INTERPRETATION: this does not promote a strategy."
    )

    def as_narrative(self) -> str:
        selected = self.selected_candidate or "(none)"
        mt = self.multiple_testing
        return (
            f"We searched {self.discovery.attempted} candidates in family {self.family_id}, "
            f"{self.discovery.failed} failed, {self.discovery.survived_discovery} survived "
            f"the discovery record, selected candidate is {selected} by pre-registration "
            f"(not max Sharpe), multiple-testing method={mt.method} "
            f"n={mt.n_hypotheses} discoveries={mt.discoveries}, "
            f"gate={self.gate.outcome.value}, data_kind={self.data_kind}. "
            f"Synthetic cannot promote. LIVE_TRADING remains false."
        )
