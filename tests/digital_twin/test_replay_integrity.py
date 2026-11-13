from __future__ import annotations

from datetime import timedelta

import pytest

from quantlab.app.digital_twin import recovery_payload
from quantlab.digital_twin.errors import ReplayMismatch, TwinCheckpointError
from quantlab.digital_twin.repository import replace
from quantlab.digital_twin.service import (
    checkpoint,
    create,
    list_runs,
    recover,
    replay,
    reset_for_tests,
    run_twin,
)
from quantlab.realtime_data.mock import SEED_AS_OF


@pytest.fixture(autouse=True)
def clean_twin() -> None:
    reset_for_tests()


def test_unknown_replay_does_not_create_a_synthetic_run() -> None:
    with pytest.raises(ReplayMismatch, match="no original"):
        replay("missing")
    assert list_runs() == []


def test_unrun_twin_cannot_be_replayed_or_checkpointed() -> None:
    original = create()
    with pytest.raises(ReplayMismatch, match="no replayable"):
        replay(original.run_id)
    with pytest.raises(TwinCheckpointError, match="no checkpointable"):
        checkpoint(original.run_id)


def test_replay_preserves_original_time() -> None:
    original = run_twin(as_of=SEED_AS_OF + timedelta(seconds=1))
    assert replay(original.run_id).events[0].event_time == original.events[0].event_time


@pytest.mark.parametrize(
    "field", ["portfolio_hash", "account_hash", "reconciliation_hash", "state_hash"]
)
def test_replay_rejects_different_components(field: str) -> None:
    original = run_twin()
    replace(original.model_copy(update={field: "changed"}))
    with pytest.raises(ReplayMismatch, match="original_run"):
        replay(original.run_id)


def test_replay_rejects_event_chain_changes() -> None:
    original = run_twin()
    changed = original.events[0].model_copy(update={"state_hash_after": "changed"})
    replace(original.model_copy(update={"events": (changed, *original.events[1:])}))
    with pytest.raises(ReplayMismatch, match="original_run"):
        replay(original.run_id)


def test_checkpoint_does_not_claim_recovery_without_state() -> None:
    original = run_twin()
    saved = checkpoint(original.run_id)
    count = len(list_runs())
    with pytest.raises(TwinCheckpointError, match="not implemented"):
        recover(saved.checkpoint_id)
    assert len(list_runs()) == count


def test_recovery_payload_exposes_safe_error_without_creating_data() -> None:
    payload = recovery_payload()
    assert "no twin run" in str(payload["error"])
    assert payload["live_trading"] is False
    assert list_runs() == []
