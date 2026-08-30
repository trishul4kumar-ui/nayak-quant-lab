"""Restart: LOAD → VERIFY HASH → RECONCILE → FRESHNESS → RESUME or ABSTAIN."""

from __future__ import annotations

from pathlib import Path

from quantlab.core.errors import CheckpointError, ShadowError
from quantlab.shadow.checkpoint import read_checkpoint
from quantlab.shadow.enums import ShadowMode
from quantlab.shadow.models import ShadowResult
from quantlab.shadow.state import put_result, set_mode


def recover(
    path: Path | None = None,
    *,
    skip_reconciliation: bool = False,
) -> ShadowResult:
    if skip_reconciliation:
        raise ShadowError("recovery_without_reconciliation is FAIL")
    checkpoint, result = read_checkpoint(path)
    stored = result.checkpoint
    if stored is None or checkpoint.payload_hash != stored.payload_hash:
        raise CheckpointError("checkpoint_hash_mismatch")
    if result.reconciliation.breaks:
        raise ShadowError("recovery refused: reconciliation_break")
    set_mode(ShadowMode.RECOVERY)
    key = str(result.extras.get("idempotency_key", checkpoint.payload_hash))
    return put_result(result, key=key)
