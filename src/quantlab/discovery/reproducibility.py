"""Replay identity. Same seed + snapshot + grammar + budget => same elite hashes."""

from __future__ import annotations

from pydantic import BaseModel

from quantlab.backtest.spec import config_hash
from quantlab.discovery.grammar import GrammarSpec
from quantlab.discovery.search import SearchBudget


class ReplayIdentity(BaseModel):
    grammar_hash: str
    budget_hash: str
    snapshot_id: str
    seed: int
    identity: str


def replay_identity(
    grammar: GrammarSpec,
    budget: SearchBudget,
    snapshot_id: str,
) -> ReplayIdentity:
    payload = {
        "grammar": grammar.identity_hash(),
        "budget": budget.identity_hash(),
        "snapshot": snapshot_id,
        "seed": budget.seed,
    }
    return ReplayIdentity(
        grammar_hash=grammar.identity_hash(),
        budget_hash=budget.identity_hash(),
        snapshot_id=snapshot_id,
        seed=budget.seed,
        identity=config_hash(payload),
    )
