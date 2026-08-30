"""Explicit candidate grids. Every generated candidate is recorded."""

from __future__ import annotations

from pydantic import BaseModel, Field

from quantlab.backtest.spec import config_hash
from quantlab.orchestration.contracts import ExperimentType
from quantlab.orchestration.errors import OrchestrationError


class SearchDimension(BaseModel):
    name: str
    values: list[int | float | str]


class SearchSpace(BaseModel):
    search_space_id: str
    version: str = "1"
    dimensions: list[SearchDimension] = Field(default_factory=list)
    notes: str = "A searched cell that is dropped is a hidden-search integrity FAIL."

    def identity_hash(self) -> str:
        return config_hash(self.model_dump(mode="json"))

    def size(self) -> int:
        n = 1
        for dim in self.dimensions:
            n *= max(len(dim.values), 1)
        return n if self.dimensions else 0


class ResearchCandidate(BaseModel):
    candidate_id: str
    search_space_id: str
    lookback: int = 20
    top_n: int = 2
    cost_bps: float = 10.0
    strategy_id: str = "cs_momentum_v1"
    experiment_type: ExperimentType = ExperimentType.DISCOVERY
    parameters: dict[str, int | float | str] = Field(default_factory=dict)
    hidden: bool = False
    failed: bool = False
    failure_reason: str = ""

    def identity_hash(self) -> str:
        return config_hash(
            {
                "candidate_id": self.candidate_id,
                "search_space_id": self.search_space_id,
                "lookback": self.lookback,
                "top_n": self.top_n,
                "cost_bps": self.cost_bps,
                "strategy_id": self.strategy_id,
                "parameters": self.parameters,
            }
        )


def expand_grid(space: SearchSpace) -> list[ResearchCandidate]:
    if not space.dimensions:
        return []
    rows: list[dict[str, int | float | str]] = [{}]
    for dim in space.dimensions:
        nxt: list[dict[str, int | float | str]] = []
        for row in rows:
            for value in dim.values:
                nxt.append({**row, dim.name: value})
        rows = nxt
    candidates: list[ResearchCandidate] = []
    for i, row in enumerate(rows):
        lookback = int(row.get("lookback", 20))
        top_n = int(row.get("top_n", 2))
        cost = float(row.get("cost_bps", 10.0))
        cid = f"{space.search_space_id}:{i:03d}:lb{lookback}:tn{top_n}:c{cost:g}"
        candidates.append(
            ResearchCandidate(
                candidate_id=cid,
                search_space_id=space.search_space_id,
                lookback=lookback,
                top_n=top_n,
                cost_bps=cost,
                parameters=dict(row),
            )
        )
    return candidates


def assert_no_hidden(candidates: list[ResearchCandidate]) -> None:
    hidden = [c.candidate_id for c in candidates if c.hidden]
    if hidden:
        raise OrchestrationError(f"hidden candidates are prohibited: {hidden}")
