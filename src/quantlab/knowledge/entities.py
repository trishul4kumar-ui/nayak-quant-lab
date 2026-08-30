"""Knowledge-graph types. Knowledge is memory, not authority."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from quantlab.backtest.spec import config_hash
from quantlab.domain.research import CheckResult


class NodeType(StrEnum):
    HYPOTHESIS = "hypothesis"
    EXPRESSION = "expression"
    FEATURE = "feature"
    FACTOR = "factor"
    ALPHA = "alpha"
    MODEL = "model"
    ADAPTIVE_LEARNER = "adaptive_learner"
    ENSEMBLE = "ensemble"
    REGIME = "regime"
    PORTFOLIO = "portfolio"
    EXPERIMENT = "experiment"
    DISCOVERY_RUN = "discovery_run"
    EVIDENCE = "evidence"
    FALSIFICATION = "falsification"
    REPLICATION = "replication"
    VALIDATION = "validation"
    DATASET_SNAPSHOT = "dataset_snapshot"
    EXECUTION_ASSUMPTION = "execution_assumption"
    RESEARCH_RESULT = "research_result"
    RESEARCH_CLAIM = "research_claim"
    DEAD_END = "dead_end"
    ALPHA_FAMILY = "alpha_family"
    CAPITAL_POLICY = "capital_policy"
    INVESTMENT_DECISION = "investment_decision"
    TARGET_PORTFOLIO = "target_portfolio"
    ORDER_INTENT = "order_intent"
    ORDER_PLAN = "order_plan"
    PAPER_ORDER = "paper_order"
    PAPER_FILL = "paper_fill"
    RECONCILIATION = "reconciliation"
    PERFORMANCE_RUN = "performance_run"
    PERFORMANCE_OBSERVATION = "performance_observation"
    ATTRIBUTION_RESULT = "attribution_result"
    RISK_OBSERVATION = "risk_observation"
    DRIFT_OBSERVATION = "drift_observation"
    RESEARCH_FEEDBACK = "research_feedback"
    DATA_SOURCE = "data_source"
    SECURITY_MASTER = "security_master"
    CORPORATE_ACTION = "corporate_action"
    TRADING_CALENDAR = "trading_calendar"
    DATA_SNAPSHOT = "data_snapshot"
    DATA_QUALITY = "data_quality"
    TCA_RUN = "tca_run"
    EXECUTION_OBSERVATION = "execution_observation"
    CALIBRATED_EXECUTION_MODEL = "calibrated_execution_model"
    LIQUIDITY_OBSERVATION = "liquidity_observation"
    CAPACITY_RESULT = "capacity_result"
    FRAGILITY_RESULT = "fragility_result"
    ECONOMETRIC_RUN = "econometric_run"
    ECONOMETRIC_ESTIMATE = "econometric_estimate"
    CAUSAL_HYPOTHESIS = "causal_hypothesis"
    STATIONARITY_TEST = "stationarity_test"
    COINTEGRATION_TEST = "cointegration_test"
    STRUCTURAL_BREAK = "structural_break"
    CERTIFICATION_CANDIDATE = "certification_candidate"
    VALIDATION_RUN = "validation_run"
    CERTIFICATION_DECISION = "certification_decision"
    MODEL_RISK_ASSESSMENT = "model_risk_assessment"
    WAIVER = "waiver"
    REPRODUCTION_RESULT = "reproduction_result"
    SHADOW_CYCLE = "shadow_cycle"
    SHADOW_DECISION = "shadow_decision"
    SHADOW_ORDER = "shadow_order"
    SHADOW_FILL = "shadow_fill"
    SHADOW_POSITION = "shadow_position"
    SHADOW_RECONCILIATION = "shadow_reconciliation"
    SHADOW_INCIDENT = "shadow_incident"
    SHADOW_ABSTENTION = "shadow_abstention"
    SAFETY_EVALUATION = "safety_evaluation"
    EXECUTION_AUTHORIZATION = "execution_authorization"
    SAFETY_INCIDENT = "safety_incident"
    KILL_EVENT = "kill_event"
    OPS_RUN = "ops_run"
    OPS_INCIDENT = "ops_incident"
    OPS_BACKUP = "ops_backup"
    OPS_RELEASE = "ops_release"
    LIVE_CERTIFICATION = "live_certification"
    RELEASE_MANIFEST = "release_manifest"
    CERTIFICATION_FINDING = "certification_finding"
    PROMOTION_EVENT = "promotion_event"
    INDEPENDENT_VALIDATION = "independent_validation"
    RELEASE_WAIVER = "release_waiver"
    BROKER_CONNECTION = "broker_connection"
    ACCOUNT_SNAPSHOT = "account_snapshot"
    BROKER_ORDER = "broker_order"
    BROKER_FILL = "broker_fill"
    BROKER_POSITION = "broker_position"
    BROKER_INCIDENT = "broker_incident"
    MARKET_OBSERVATION = "market_observation"
    REALTIME_SNAPSHOT = "realtime_snapshot"
    STRATEGY_RELEASE = "strategy_release"
    REALTIME_DECISION = "realtime_decision"
    TWIN_RUN = "twin_run"
    TWIN_EVENT = "twin_event"
    TWIN_CHECKPOINT = "twin_checkpoint"
    COUNTERFACTUAL = "counterfactual"


class RelationType(StrEnum):
    DERIVED_FROM = "derived_from"
    MUTATED_FROM = "mutated_from"
    CROSSED_FROM = "crossed_from"
    SIMPLIFIED_FROM = "simplified_from"
    GENERALIZED_FROM = "generalized_from"
    SPECIALIZED_FROM = "specialized_from"
    RESIDUALIZED_FROM = "residualized_from"
    ENSEMBLED_FROM = "ensembled_from"
    STACKED_FROM = "stacked_from"
    FALSIFIED_BY = "falsified_by"
    REPLICATED_BY = "replicated_by"
    SUPERSEDES = "supersedes"
    DUPLICATES = "duplicates"
    CONTRADICTS = "contradicts"
    SUPPORTS = "supports"
    USES_FEATURE = "uses_feature"
    TESTED_BY = "tested_by"
    EVIDENCE_FOR = "evidence_for"
    MEMBER_OF = "member_of"
    PRODUCED_BY = "produced_by"


class HypothesisStatus(StrEnum):
    PROPOSED = "proposed"
    PRE_REGISTERED = "pre_registered"
    UNDER_TEST = "under_test"
    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    FALSIFIED = "falsified"
    REJECTED = "rejected"
    REPLICATED = "replicated"
    VALIDATED = "validated"
    STALE = "stale"
    SUPERSEDED = "superseded"
    DUPLICATE = "duplicate"
    INCONCLUSIVE = "inconclusive"
    NOT_TESTED = "not_tested"


class EvidenceType(StrEnum):
    DISCOVERY_EVIDENCE = "discovery_evidence"
    IN_SAMPLE_EVIDENCE = "in_sample_evidence"
    OOS_EVIDENCE = "oos_evidence"
    WALK_FORWARD_EVIDENCE = "walk_forward_evidence"
    ROBUSTNESS_EVIDENCE = "robustness_evidence"
    STATISTICAL_EVIDENCE = "statistical_evidence"
    EXECUTION_EVIDENCE = "execution_evidence"
    REGIME_EVIDENCE = "regime_evidence"
    RISK_EVIDENCE = "risk_evidence"
    REPLICATION_EVIDENCE = "replication_evidence"
    FALSIFICATION_EVIDENCE = "falsification_evidence"
    ABLATION_EVIDENCE = "ablation_evidence"
    SENSITIVITY_EVIDENCE = "sensitivity_evidence"
    NULL_EVIDENCE = "null_evidence"


class ClaimStatus(StrEnum):
    UNSUPPORTED = "unsupported"
    PRELIMINARY = "preliminary"
    SUPPORTED = "supported"
    REPLICATED = "replicated"
    VALIDATED = "validated"
    CONTRADICTED = "contradicted"
    FALSIFIED = "falsified"


class SimilarityClass(StrEnum):
    IDENTICAL = "identical"
    HIGH_REDUNDANCY = "high_redundancy"
    RELATED = "related"
    WEAKLY_RELATED = "weakly_related"
    DISTINCT = "distinct"
    UNKNOWN = "unknown"


class NoveltyHint(StrEnum):
    KNOWN = "known"
    RELATED = "related"
    NOVEL = "novel"
    UNKNOWN = "unknown"


class ReplicationKind(StrEnum):
    EXACT_REPLICATION = "exact_replication"
    TEMPORAL_REPLICATION = "temporal_replication"
    DATASET_REPLICATION = "dataset_replication"
    UNIVERSE_REPLICATION = "universe_replication"
    REGIME_REPLICATION = "regime_replication"
    EXECUTION_REPLICATION = "execution_replication"
    METHODOLOGICAL_REPLICATION = "methodological_replication"


class ContentOrigin(StrEnum):
    EMPIRICAL = "empirical"
    AI_GENERATED_HYPOTHESIS = "ai_generated_hypothesis"
    AI_GENERATED_SUMMARY = "ai_generated_summary"
    AI_GENERATED_RESEARCH_SUGGESTION = "ai_generated_research_suggestion"


class KnowledgeNode(BaseModel):
    node_id: str
    node_type: NodeType
    canonical_identity: str = ""
    version: str = "1"
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    status: str = "recorded"
    source: str = "seed"
    config_hash: str = ""
    content_hash: str = ""
    metadata: dict[str, str] = Field(default_factory=dict)
    origin: ContentOrigin = ContentOrigin.EMPIRICAL
    ref_id: str = ""

    def identity_payload(self) -> dict[str, object]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "version": self.version,
            "status": self.status,
            "source": self.source,
            "ref_id": self.ref_id,
            "origin": self.origin.value,
            "metadata": dict(sorted(self.metadata.items())),
        }

    def compute_hashes(self) -> KnowledgeNode:
        digest = config_hash(self.identity_payload())
        return self.model_copy(
            update={
                "canonical_identity": digest,
                "content_hash": digest,
                "config_hash": digest,
            }
        )


class KnowledgeEdge(BaseModel):
    edge_id: str
    source_id: str
    target_id: str
    relationship_type: RelationType
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    source_experiment_id: str = ""
    evidence_id: str = ""
    confidence_basis: str = "recorded"
    metadata: dict[str, str] = Field(default_factory=dict)

    def identity_payload(self) -> dict[str, object]:
        return {
            "edge_id": self.edge_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relationship_type": self.relationship_type.value,
            "source_experiment_id": self.source_experiment_id,
            "evidence_id": self.evidence_id,
            "confidence_basis": self.confidence_basis,
            "metadata": dict(sorted(self.metadata.items())),
        }


class HypothesisRecord(BaseModel):
    hypothesis_id: str
    title: str
    statement: str
    formal_expression: str = ""
    expected_direction: str = ""
    economic_rationale: str = ""
    mathematical_rationale: str = ""
    source_type: str = "human"
    parent_hypothesis_id: str = ""
    discovery_id: str = ""
    pre_registration_id: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    status: HypothesisStatus = HypothesisStatus.PROPOSED
    origin: ContentOrigin = ContentOrigin.EMPIRICAL


class EvidenceRecord(BaseModel):
    evidence_id: str
    experiment_id: str
    hypothesis_id: str
    dataset_id: str = ""
    snapshot_checksum: str = ""
    config_hash: str = ""
    result_type: EvidenceType = EvidenceType.IN_SAMPLE_EVIDENCE
    metric: str = ""
    metric_value: float | None = None
    sample_size: int = 0
    coverage: float | None = None
    train_period: str = ""
    validation_period: str = ""
    test_period: str = ""
    regime_context: str = ""
    execution_assumption: str = ""
    integrity_status: CheckResult = CheckResult.NOT_TESTED
    gate_status: str = ""
    data_kind: str = "synthetic"
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    origin: ContentOrigin = ContentOrigin.EMPIRICAL
    limitations: list[str] = Field(default_factory=list)


class ResearchClaim(BaseModel):
    claim_id: str
    hypothesis_id: str
    statement: str
    support_evidence_ids: list[str] = Field(default_factory=list)
    dataset_id: str = ""
    status: ClaimStatus = ClaimStatus.UNSUPPORTED
    limitations: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    knowledge_as_of: str = ""
    origin: ContentOrigin = ContentOrigin.EMPIRICAL
    superseded_by: str = ""


class ReplicationRecord(BaseModel):
    replication_id: str
    kind: ReplicationKind
    original_hypothesis: str
    original_experiment: str
    replication_experiment: str
    dataset_difference: str = ""
    time_period_difference: str = ""
    feature_difference: str = ""
    execution_difference: str = ""
    result_comparison: str = ""
    original_snapshot: str = ""
    replication_snapshot: str = ""
    original_protocol: str = ""
    replication_protocol: str = ""


class AlphaFamily(BaseModel):
    family_id: str
    title: str
    member_ids: list[str] = Field(default_factory=list)
    parent: str = ""
    failed_members: list[str] = Field(default_factory=list)
    surviving_members: list[str] = Field(default_factory=list)


class SearchAccounting(BaseModel):
    family_id: str
    search_space_id: str = ""
    candidate_count: int = 0
    tested_count: int = 0
    rejected_count: int = 0
    falsified_count: int = 0
    selected_count: int = 0
    pruned_count: int = 0
    duplicate_count: int = 0
    stopping_reason: str = "frozen_budget"
    selection_policy: str = ""


class KnowledgeSnapshot(BaseModel):
    knowledge_snapshot_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    graph_hash: str
    node_count: int
    edge_count: int
    software_version: str
    schema_version: str = "1"
    payload: dict[str, object] = Field(default_factory=dict)
