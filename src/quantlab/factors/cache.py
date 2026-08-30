"""Factor cache keys. Hits must include snapshot, universe, and identity."""

from __future__ import annotations

from datetime import datetime

from quantlab.backtest.spec import config_hash
from quantlab.factors.definition import FactorDefinition
from quantlab.research.cache import ResultCache


def factor_cache_key(
    definition: FactorDefinition,
    *,
    snapshot_id: str,
    universe: list[str],
    start: datetime | None,
    end: datetime | None,
) -> str:
    return config_hash(
        {
            "identity": definition.identity_hash(),
            "snapshot_id": snapshot_id,
            "universe": sorted(universe),
            "start": None if start is None else start.isoformat(),
            "end": None if end is None else end.isoformat(),
        }
    )


FACTOR_CACHE = ResultCache()
