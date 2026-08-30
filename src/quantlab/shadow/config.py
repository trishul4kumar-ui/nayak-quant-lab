"""Immutable shadow configuration identity."""

from __future__ import annotations

from quantlab.shadow.enums import ShadowMode
from quantlab.shadow.identity import hash_config
from quantlab.shadow.models import ShadowConfig


def make_config(
    *,
    mode: ShadowMode = ShadowMode.RESEARCH_PAPER,
    strategy_version: str = "seed-v1",
    execution_policy: str = "base",
    max_data_age_ms: int = 300_000,
    data_source: str = "synthetic_seed",
) -> ShadowConfig:
    base = ShadowConfig(
        mode=mode,
        strategy_version=strategy_version,
        execution_policy=execution_policy,
        max_data_age_ms=max_data_age_ms,
        data_source=data_source,
        model_versions={"paper_oms": "prompt-18", "execution_research": "prompt-13"},
    )
    return base.model_copy(update={"configuration_hash": hash_config(base)})
