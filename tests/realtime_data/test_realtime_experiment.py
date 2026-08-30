from __future__ import annotations

from pathlib import Path

from quantlab.digital_twin.experiment import run_twin_experiment
from quantlab.realtime_data.experiment import run_realtime_experiment
from quantlab.realtime_decision.experiment import run_decision_experiment


def test_ledger_rows(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.jsonl"
    frozen, row = run_realtime_experiment(ledger_path=ledger)
    assert row.realtime_snapshot_hash == frozen.snapshot_hash
    assert row.selection_stage == "realtime_data"
    decided, drow = run_decision_experiment(ledger_path=ledger)
    assert drow.realtime_decision_hash == decided.decision_hash
    twin, trow = run_twin_experiment(ledger_path=ledger)
    assert trow.twin_state_hash == twin.state_hash
    assert trow.release_blocked is True
