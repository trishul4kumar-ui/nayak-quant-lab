"""Feature cache keys. A hit must include every input that changes the result."""

from __future__ import annotations

from datetime import datetime

from quantlab.backtest.spec import config_hash
from quantlab.features.definition import FeatureDefinition
from quantlab.research.cache import ResultCache


def feature_cache_key(
    definition: FeatureDefinition,
    *,
    snapshot_id: str,
    universe: list[str],
    start: datetime | None,
    end: datetime | None,
    frequency: str,
    normalization: str,
) -> str:
    return config_hash(
        {
            "identity": definition.identity_hash(),
            "operator_version": definition.implementation_version,
            "snapshot_id": snapshot_id,
            "universe": sorted(universe),
            "start": None if start is None else start.isoformat(),
            "end": None if end is None else end.isoformat(),
            "frequency": frequency,
            "normalization": normalization,
        }
    )


FEATURE_CACHE = ResultCache()
