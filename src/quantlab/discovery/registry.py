"""Seed discovery families. Registration is not evidence."""

from __future__ import annotations

from pydantic import BaseModel, Field

from quantlab.discovery.errors import DiscoveryError
from quantlab.discovery.grammar import GrammarSpec
from quantlab.discovery.search import SearchBudget


class DiscoveryFamily(BaseModel):
    family_id: str
    title: str
    grammar: GrammarSpec = Field(default_factory=GrammarSpec)
    budget: SearchBudget = Field(default_factory=SearchBudget)
    hypothesis_id: str = "H-DISC-001"
    note: str = "Diagnostic family. Synthetic results are not market evidence."


class DiscoveryRegistry:
    def __init__(self) -> None:
        self._families: dict[str, DiscoveryFamily] = {}
        self.register(
            DiscoveryFamily(
                family_id="GP-MOM-VOL-001",
                title="Momentum / volatility symbolic search",
                grammar=GrammarSpec(max_depth=4, max_nodes=15, max_constants=2),
                budget=SearchBudget(population_size=8, n_generations=3, max_candidates=24),
            )
        )

    def register(self, family: DiscoveryFamily) -> None:
        if family.family_id in self._families:
            raise DiscoveryError(f"cannot overwrite family {family.family_id}")
        self._families[family.family_id] = family

    def get(self, family_id: str) -> DiscoveryFamily:
        found = self._families.get(family_id)
        if found is None:
            raise DiscoveryError(f"unknown family {family_id}")
        return found

    def list(self) -> list[DiscoveryFamily]:
        return list(self._families.values())


_DEFAULT = DiscoveryRegistry()


def default_registry() -> DiscoveryRegistry:
    return _DEFAULT


def get_family(family_id: str) -> DiscoveryFamily:
    return _DEFAULT.get(family_id)


def list_families() -> list[DiscoveryFamily]:
    return _DEFAULT.list()
