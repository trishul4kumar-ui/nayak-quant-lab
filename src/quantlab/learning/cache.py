"""Learning cache keys. Hits must include identity, snapshot, window, and seed."""

from __future__ import annotations

from datetime import datetime

from quantlab.backtest.spec import config_hash
from quantlab.learning.definition import ModelDefinition
from quantlab.research.cache import ResultCache


def learning_cache_key(
    model: ModelDefinition,
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
            "window": model.training_window,
            "normalization": model.normalization.value,
            "selection": model.selection_method.value,
            "seed": seed,
            "software": model.implementation_version,
        }
    )


LEARNING_CACHE = ResultCache()
