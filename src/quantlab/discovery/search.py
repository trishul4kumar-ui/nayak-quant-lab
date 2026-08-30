"""Frozen search. Budget and stopping cannot be rewritten after seeing results."""

from __future__ import annotations

from pydantic import BaseModel

from quantlab.backtest.spec import config_hash
from quantlab.discovery.errors import DiscoveryError


class SearchBudget(BaseModel):
    population_size: int = 8
    n_generations: int = 3
    max_candidates: int = 24
    tournament_k: int = 3
    elite: int = 1
    seed: int = 7
    frozen: bool = True

    def identity_hash(self) -> str:
        return config_hash(self.model_dump(mode="json"))


def assert_budget_frozen(declared: SearchBudget, used: SearchBudget) -> None:
    if declared.identity_hash() != used.identity_hash():
        raise DiscoveryError("search budget mutated after freeze")
    if used.max_candidates < used.population_size:
        raise DiscoveryError("max_candidates smaller than population")
