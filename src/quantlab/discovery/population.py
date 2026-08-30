"""Search population. Every generated candidate is kept."""

from __future__ import annotations

from pydantic import BaseModel, Field

from quantlab.discovery.definitions import CandidateStatus, NoveltyClass, SearchMode
from quantlab.discovery.expression import ExprNode
from quantlab.discovery.fitness import FitnessVector


class DiscoveryCandidate(BaseModel):
    candidate_id: str
    expression: ExprNode
    expression_hash: str
    canonical_text: str
    generation: int = 0
    parents: list[str] = Field(default_factory=list)
    origin: SearchMode = SearchMode.SEEDED
    status: CandidateStatus = CandidateStatus.GENERATED
    novelty: NoveltyClass = NoveltyClass.NOVEL
    fitness: FitnessVector | None = None
    mutation: str = ""
    note: str = ""


class Population(BaseModel):
    members: list[DiscoveryCandidate] = Field(default_factory=list)

    def by_hash(self) -> dict[str, DiscoveryCandidate]:
        return {item.expression_hash: item for item in self.members}
