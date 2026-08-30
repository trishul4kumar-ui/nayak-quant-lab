from __future__ import annotations

from pathlib import Path

import pytest

from quantlab.release.experiment import run_release_experiment
from quantlab.release.service import default_passing_request, evaluate

pytestmark = pytest.mark.release


def test_failed_attempts_are_retained() -> None:
    first = evaluate()
    second = evaluate()
    assert first.evaluation_id == second.evaluation_id
    from quantlab.release.audit import history

    assert len(history()) >= 2


def test_ledger_selection_stage(tmp_path: Path) -> None:
    result, row = run_release_experiment(
        default_passing_request(),
        ledger_path=tmp_path / "ledger.jsonl",
    )
    assert row.selection_stage == "certification"
    assert row.live_certification_id == result.evaluation_id
    assert row.release_blocked is True
    assert result.live_enabled is False
