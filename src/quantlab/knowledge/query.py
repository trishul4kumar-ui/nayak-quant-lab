"""Knowledge query API. Read-only over the graph."""

from __future__ import annotations

from quantlab.discovery.expression import ExprNode
from quantlab.knowledge.entities import (
    EvidenceRecord,
    HypothesisRecord,
    KnowledgeNode,
    NodeType,
    RelationType,
    ResearchClaim,
    SimilarityClass,
)
from quantlab.knowledge.graph import KnowledgeGraph
from quantlab.knowledge.indexing import KnowledgeIndex
from quantlab.knowledge.lineage import LineagePath
from quantlab.knowledge.similarity import expression_similarity
from quantlab.knowledge.status import detect_contradictions


def find_hypothesis(graph: KnowledgeGraph, hypothesis_id: str) -> HypothesisRecord | None:
    for item in graph.hypotheses:
        if item.hypothesis_id == hypothesis_id:
            return item
    return None


def find_related_hypotheses(graph: KnowledgeGraph, hypothesis_id: str) -> list[str]:
    node_id = f"hypothesis:{hypothesis_id}"
    return [item for item in graph.walk(node_id) if item.startswith("hypothesis:")]


def find_similar_expression(left: ExprNode, right: ExprNode) -> SimilarityClass:
    return expression_similarity(left, right)


def find_alpha_family(graph: KnowledgeGraph, family_id: str) -> list[str]:
    for family in graph.families:
        if family.family_id == family_id:
            return list(family.member_ids)
    return []


def find_lineage(graph: KnowledgeGraph, node_id: str, *, reverse: bool = False) -> LineagePath:
    from quantlab.knowledge.lineage import find_lineage as walk_lineage

    return walk_lineage(graph, node_id, reverse=reverse)


def find_evidence(graph: KnowledgeGraph, hypothesis_id: str) -> list[EvidenceRecord]:
    return [item for item in graph.evidence if item.hypothesis_id == hypothesis_id]


def find_failures(graph: KnowledgeGraph, _query: str = "") -> list[KnowledgeNode]:
    return [
        item
        for item in graph.nodes
        if item.node_type is NodeType.DEAD_END or item.status in {"falsified", "failed", "rejected"}
    ]


def find_dead_ends(graph: KnowledgeGraph) -> list[KnowledgeNode]:
    return [item for item in graph.nodes if item.node_type is NodeType.DEAD_END]


def find_replications(graph: KnowledgeGraph, hypothesis_id: str = "") -> list[str]:
    rows = graph.replications
    if hypothesis_id:
        rows = [item for item in rows if item.original_hypothesis == hypothesis_id]
    return [item.replication_id for item in rows]


def find_contradictions(graph: KnowledgeGraph) -> list[tuple[ResearchClaim, ResearchClaim]]:
    return detect_contradictions(graph)


def find_research_claims(graph: KnowledgeGraph, hypothesis_id: str = "") -> list[ResearchClaim]:
    if not hypothesis_id:
        return list(graph.claims)
    return [item for item in graph.claims if item.hypothesis_id == hypothesis_id]


def find_dependencies(graph: KnowledgeGraph, node_id: str) -> list[str]:
    return [
        edge.target_id
        for edge in graph.edges
        if edge.source_id == node_id
        and edge.relationship_type
        in {RelationType.USES_FEATURE, RelationType.DERIVED_FROM, RelationType.PRODUCED_BY}
    ]


def find_dependents(graph: KnowledgeGraph, node_id: str) -> list[str]:
    return [edge.source_id for edge in graph.edges if edge.target_id == node_id]


def find_by_dataset(graph: KnowledgeGraph, dataset_id: str) -> list[EvidenceRecord]:
    return [item for item in graph.evidence if item.dataset_id == dataset_id]


def find_by_regime(graph: KnowledgeGraph, regime: str) -> list[EvidenceRecord]:
    return [item for item in graph.evidence if item.regime_context == regime]


def find_by_feature(graph: KnowledgeGraph, feature_id: str) -> list[str]:
    nid = f"feature:{feature_id}"
    return find_dependents(graph, nid)


def find_by_factor(graph: KnowledgeGraph, factor_id: str) -> list[str]:
    return find_dependents(graph, f"factor:{factor_id}")


def find_by_experiment(graph: KnowledgeGraph, experiment_id: str) -> list[EvidenceRecord]:
    return [item for item in graph.evidence if item.experiment_id == experiment_id]


def find_by_status(graph: KnowledgeGraph, status: str) -> list[KnowledgeNode]:
    return KnowledgeIndex(graph).by_status.get(status, [])
