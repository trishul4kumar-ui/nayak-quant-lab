"""Freeze the exact inputs of a cycle. Mutation after freeze is FAIL."""

from __future__ import annotations

from datetime import datetime

from quantlab.paper_oms.models import PaperAccount, PaperMarketSnapshot
from quantlab.shadow.identity import hash_snapshot
from quantlab.shadow.models import FrozenSnapshot, ShadowConfig


def freeze_snapshot(
    snapshot: PaperMarketSnapshot,
    *,
    account: PaperAccount,
    config: ShadowConfig,
    decision_time: datetime,
    extra_hashes: dict[str, str] | None = None,
) -> FrozenSnapshot:
    del decision_time
    hashes = extra_hashes or {}
    frozen = FrozenSnapshot(
        snapshot_id=snapshot.snapshot_id,
        snapshot_hash="",
        market_data_hash=hashes.get("market", snapshot.snapshot_id),
        feature_snapshot_hash=hashes.get("feature", ""),
        factor_state_hash=hashes.get("factor", ""),
        regime_state_hash=hashes.get("regime", ""),
        model_state_hash=hashes.get("model", ""),
        adaptive_state_hash=hashes.get("adaptive", ""),
        ensemble_state_hash=hashes.get("ensemble", ""),
        risk_state_hash=hashes.get("risk", ""),
        capital_policy_hash=hashes.get("capital", config.capital_policy),
        portfolio_state_hash=hashes.get("portfolio", account.account_id),
        execution_policy_hash=hashes.get("execution", config.execution_policy),
        configuration_hash=config.configuration_hash,
        as_of=snapshot.as_of,
    )
    return frozen.model_copy(update={"snapshot_hash": hash_snapshot(frozen)})
