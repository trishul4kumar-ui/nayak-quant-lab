"""Execution cache keys. Hits include identity, snapshot, scenario, capital, seed."""

from __future__ import annotations

from quantlab.backtest.spec import config_hash
from quantlab.execution_research.definition import MarketMicrostructureDefinition
from quantlab.research.cache import ResultCache


def execution_cache_key(
    definition: MarketMicrostructureDefinition,
    *,
    snapshot_id: str,
    capital: float,
    scenario_id: str,
    seed: int,
) -> str:
    return config_hash(
        {
            "identity": definition.identity_hash(),
            "snapshot_id": snapshot_id,
            "capital": capital,
            "scenario_id": scenario_id,
            "seed": seed,
            "software": definition.implementation_version,
        }
    )


EXECUTION_CACHE = ResultCache()
