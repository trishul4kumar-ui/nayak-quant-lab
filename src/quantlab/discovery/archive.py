"""Immutable candidate archive. Losers stay."""

from __future__ import annotations

from pydantic import BaseModel, Field

from quantlab.discovery.errors import DiscoveryError
from quantlab.discovery.population import DiscoveryCandidate


class CandidateArchive(BaseModel):
    items: list[DiscoveryCandidate] = Field(default_factory=list)

    def add(self, candidate: DiscoveryCandidate) -> None:
        self.items.append(candidate)

    def hashes(self) -> set[str]:
        return {item.expression_hash for item in self.items}

    def refuse_overwrite(self, expression_hash: str) -> None:
        if expression_hash in self.hashes():
            raise DiscoveryError("archive overwrite is prohibited; record a new generation row")
