"""Query lineage: where did this expression come from?"""

from __future__ import annotations

from pydantic import BaseModel, Field

from quantlab.discovery.population import DiscoveryCandidate


class LineageNode(BaseModel):
    candidate_id: str
    expression_hash: str
    generation: int
    parents: list[str] = Field(default_factory=list)
    canonical_text: str = ""


class DiscoveryLineage(BaseModel):
    family_id: str
    nodes: list[LineageNode] = Field(default_factory=list)

    def broken(self) -> bool:
        known = {node.candidate_id for node in self.nodes} | {
            node.expression_hash for node in self.nodes
        }
        for node in self.nodes:
            for parent in node.parents:
                if parent and parent not in known and not parent.startswith("seed:"):
                    return True
        return False


def build_lineage(family_id: str, candidates: list[DiscoveryCandidate]) -> DiscoveryLineage:
    nodes = [
        LineageNode(
            candidate_id=item.candidate_id,
            expression_hash=item.expression_hash,
            generation=item.generation,
            parents=list(item.parents),
            canonical_text=item.canonical_text,
        )
        for item in candidates
    ]
    return DiscoveryLineage(family_id=family_id, nodes=nodes)
