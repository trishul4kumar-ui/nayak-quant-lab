"""Knowledge leak flags. Actual PASS/FAIL lives in quantlab.research.integrity."""

from __future__ import annotations

from pydantic import BaseModel


class KnowledgeLeakFlags(BaseModel):
    knowledge_provenance_break: bool | None = None
    evidence_without_experiment: bool | None = None
    claim_without_evidence: bool | None = None
    claim_overstates_evidence: bool | None = None
    lineage_break: bool | None = None
    candidate_history_deleted: bool | None = None
    duplicate_identity_collision: bool | None = None
    snapshot_mutation: bool | None = None
    historical_claim_mutation: bool | None = None
    future_knowledge_leak: bool | None = None
    future_claim_context: bool | None = None
    replication_same_data: bool | None = None
    contradiction_hidden: bool | None = None
    search_degree_of_freedom_loss: bool | None = None
    synthetic_evidence_overpromotion: bool | None = None
    ai_evidence_confusion: bool | None = None
