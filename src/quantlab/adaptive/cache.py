"""Adaptive cache keys. Hits must include identity, snapshot, window, and seed."""

from __future__ import annotations

from datetime import datetime

from quantlab.adaptive.definition import AdaptiveModelDefinition
from quantlab.backtest.spec import config_hash
from quantlab.research.cache import ResultCache


def adaptive_cache_key(
    model: AdaptiveModelDefinition,
    *,
    snapshot_id: str,
    universe: list[str],
    start: datetime | None,
    end: datetime | None,
    seed: int,
) -> str:
    return config_hash(
        {
            "identity": model.identity_hash(),
            "snapshot_id": snapshot_id,
            "universe": sorted(universe),
            "start": None if start is None else start.isoformat(),
            "end": None if end is None else end.isoformat(),
            "window": model.window,
            "half_life": model.half_life,
            "seed": seed,
        }
    )


ADAPTIVE_CACHE = ResultCache()
