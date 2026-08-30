"""Regime cache keys. Hits must include snapshot, universe, and identity."""

from __future__ import annotations

from datetime import datetime

from quantlab.backtest.spec import config_hash
from quantlab.regimes.definition import RegimeModel
from quantlab.research.cache import ResultCache


def regime_cache_key(
    model: RegimeModel,
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
            "seed": seed,
        }
    )


REGIME_CACHE = ResultCache()
