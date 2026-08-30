"""Ensemble cache keys. Hits must include identity, snapshot, window, and seed."""

from __future__ import annotations

from datetime import datetime

from quantlab.backtest.spec import config_hash
from quantlab.ensemble.definition import EnsembleDefinition
from quantlab.research.cache import ResultCache


def ensemble_cache_key(
    definition: EnsembleDefinition,
    *,
    snapshot_id: str,
    universe: list[str],
    start: datetime | None,
    end: datetime | None,
    seed: int,
) -> str:
    return config_hash(
        {
            "identity": definition.identity_hash(),
            "snapshot_id": snapshot_id,
            "universe": sorted(universe),
            "start": None if start is None else start.isoformat(),
            "end": None if end is None else end.isoformat(),
            "window": definition.training_window,
            "normalization": definition.normalization.value,
            "weighting": definition.weighting_policy.value,
            "regime": definition.regime_model_id,
            "adaptive": definition.adaptive_policy,
            "seed": seed,
            "software": definition.implementation_version,
        }
    )


ENSEMBLE_CACHE = ResultCache()
