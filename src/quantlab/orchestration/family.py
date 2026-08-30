"""Research families and researcher degrees of freedom."""

from __future__ import annotations

from pydantic import BaseModel

from quantlab.backtest.spec import config_hash
from quantlab.orchestration.contracts import SelectionPolicy, StoppingPolicy
from quantlab.orchestration.search_space import SearchSpace


class ResearchFamily(BaseModel):
    family_id: str
    version: str = "1"
    hypothesis_id: str
    search_space_id: str
    baseline_id: str = "equal_weight"
    selection_policy: SelectionPolicy = SelectionPolicy.PRE_REGISTERED
    stopping_policy: StoppingPolicy = StoppingPolicy.PRE_REGISTERED_BUDGET
    multiple_testing_method: str = "benjamini_hochberg"
    notes: str = "Family membership is the multiple-testing unit. Dropping a loser is a FAIL."

    def identity_hash(self) -> str:
        return config_hash(self.model_dump(mode="json"))


class DegreesOfFreedom(BaseModel):
    family_id: str
    search_cells: int
    free_parameters: int
    interventions: int = 0
    tested_count: int = 0
    hidden_count: int = 0
    note: str = "Degrees of freedom are a research-cost, not a Sharpe bonus."


def degrees_of_freedom(
    family: ResearchFamily,
    space: SearchSpace,
    *,
    tested_count: int,
    interventions: int = 0,
    hidden_count: int = 0,
) -> DegreesOfFreedom:
    return DegreesOfFreedom(
        family_id=family.family_id,
        search_cells=space.size(),
        free_parameters=sum(max(len(d.values) - 1, 0) for d in space.dimensions),
        interventions=interventions,
        tested_count=tested_count,
        hidden_count=hidden_count,
    )
