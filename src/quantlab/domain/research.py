"""Research objects: hypothesis, genome, alpha, lineage, status. Not broker types."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ResearchStatus(StrEnum):
    IDEA = "idea"
    FORMALIZED = "formalized"
    EXPERIMENTAL = "experimental"
    PROPOSED = "proposed"
    TESTING = "testing"
    SUPPORTED = "supported"
    PROMISING = "promising"
    ROBUST = "robust"
    PAPER = "paper"
    LIVE_CANDIDATE = "live_candidate"
    LIVE = "live"
    DEGRADED = "degraded"
    RETIRED = "retired"
    REJECTED = "rejected"
    CONTAMINATED = "contaminated"
    DEPRECATED = "deprecated"


class ModelLifecycle(StrEnum):
    CREATED = "created"
    TRAINED = "trained"
    VALIDATED = "validated"
    BACKTESTED = "backtested"
    STRESS_TESTED = "stress_tested"
    RESEARCH_APPROVED = "research_approved"
    PAPER_APPROVED = "paper_approved"
    LIVE_APPROVED = "live_approved"
    ACTIVE = "active"
    RETIRED = "retired"


class CheckResult(StrEnum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    NOT_TESTED = "not_tested"


class Feature(BaseModel):
    name: str
    version: str
    value: float
    as_of: datetime


class Factor(BaseModel):
    name: str
    version: str
    family: str = "momentum"
    description: str = ""


class ExpressionNode(BaseModel):
    """Tiny AST. No genetic search and no unrestricted Python eval."""

    op: str
    name: str | None = None
    child: ExpressionNode | None = None
    right: ExpressionNode | None = None
    weight: float | None = None


class SignalGenome(BaseModel):
    genome_id: str
    version: str = "0.1.0"
    inputs: list[str]
    expression: ExpressionNode
    prediction_horizon: str = "1d"
    holding_period: str = "1d"
    direction: str = "long_high_rank"
    neutralization: str = "none"
    provenance: str = ""


class ResearchHypothesis(BaseModel):
    id: str
    title: str
    statement: str
    economic_intuition: str = ""
    mathematical_formulation: str = ""
    expected_effect: str = ""
    universe: list[str] = Field(default_factory=list)
    time_horizon: str = "1d"
    required_data: list[str] = Field(default_factory=list)
    potential_confounders: list[str] = Field(default_factory=list)
    null_hypothesis: str = ""
    alternative_hypothesis: str = ""
    experiment_design: str = ""
    acceptance_criteria: str = ""
    rejection_criteria: str = ""
    researcher: str = "quantlab"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    version: str = "0.1.0"
    status: ResearchStatus = ResearchStatus.EXPERIMENTAL
    expected_direction: str = ""
    expected_horizon: str = ""
    pre_registered: bool = False


class Alpha(BaseModel):
    alpha_id: str
    name: str
    hypothesis_id: str
    universe: list[str]
    data_dependencies: list[str]
    features: list[str]
    signal_definition: str
    prediction_horizon: str
    holding_period: str
    expected_direction: str = "long"
    neutralization: str = "none"
    constraints: list[str] = Field(default_factory=list)
    validation_protocol: str = "next_bar_cost_adjusted"
    research_status: ResearchStatus = ResearchStatus.EXPERIMENTAL
    version: str = "0.1.0"
    provenance: str = ""
    genome_id: str = ""


class DataLineage(BaseModel):
    provider: str
    dataset_version: str
    ingested_at: datetime
    transformations: list[str] = Field(default_factory=list)
    feature_versions: dict[str, str] = Field(default_factory=dict)
    signal_version: str = ""
    model_version: str | None = None
    genome_id: str = ""
    dataset_id: str = ""
    snapshot_id: str = ""
    data_kind: str = "synthetic"
    checksum: str = ""
    source: str = ""

    def as_dict(self) -> dict[str, str]:
        features = ",".join(f"{k}={v}" for k, v in self.feature_versions.items())
        return {
            "provider": self.provider,
            "dataset_version": self.dataset_version,
            "ingested_at": self.ingested_at.isoformat(),
            "transformations": ",".join(self.transformations),
            "feature_versions": features,
            "signal_version": self.signal_version,
            "model_version": self.model_version or "",
            "genome_id": self.genome_id,
            "dataset_id": self.dataset_id,
            "snapshot_id": self.snapshot_id,
            "data_kind": self.data_kind,
            "checksum": self.checksum,
            "source": self.source,
        }


class IntegrityReport(BaseModel):
    checks: dict[str, CheckResult] = Field(default_factory=dict)
    notes: dict[str, str] = Field(default_factory=dict)

    def as_str_map(self) -> dict[str, str]:
        return {name: result.value for name, result in self.checks.items()}

    def failed(self) -> bool:
        return any(v is CheckResult.FAIL for v in self.checks.values())
