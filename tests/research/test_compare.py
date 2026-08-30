from datetime import UTC, datetime
from pathlib import Path

from quantlab.core.identifiers import InstrumentId
from quantlab.core.time import PointInTime
from quantlab.domain.models import ExperimentRun, ExperimentStatus, OHLCVBar, Signal
from quantlab.models.registry import ExperimentLedger
from quantlab.research.compare import compare_runs
from quantlab.research.cross_section import spearman_ic
from quantlab.research.decay import signal_decay


def test_spearman_ic_perfect_ranks() -> None:
    scores = {"a": 3.0, "b": 2.0, "c": 1.0}
    fwd = {"a": 0.3, "b": 0.2, "c": 0.1}
    ic = spearman_ic(scores, fwd)
    assert ic is not None
    assert ic > 0.99


def test_signal_decay_horizons() -> None:
    day0 = datetime(2024, 1, 2, tzinfo=UTC)
    inst = InstrumentId.parse("NSE:TCS")
    bars = []
    for i in range(6):
        day = datetime(2024, 1, 2 + i, tzinfo=UTC)
        pit = PointInTime(
            event_time=day, effective_time=day, available_time=day, ingestion_time=day
        )
        bars.append(
            OHLCVBar(instrument=inst, pit=pit, open=10 + i, high=11 + i, low=9 + i, close=10 + i)
        )
    report = signal_decay(
        {inst: bars},
        {day0: [Signal(instrument=inst, score=1.0, as_of=day0)]},
        horizons=(1, 2),
    )
    assert [p.horizon for p in report.points] == [1, 2]


def test_compare_and_ledger_get(tmp_path: Path) -> None:
    path = tmp_path / "ledger.jsonl"
    ledger = ExperimentLedger(path)
    run = ExperimentRun(
        id="abc123",
        name="one",
        hypothesis="h",
        status=ExperimentStatus.PASSED,
        dataset_version="v1",
        universe=["NSE:TCS"],
        gate_outcome="warn",
        metrics={
            "sharpe": 0.1,
            "total_return": 0.02,
            "max_drawdown": -0.01,
            "mean_turnover": 0.1,
        },
        transaction_cost_bps=10.0,
    )
    other = run.model_copy(update={"id": "def456", "name": "two"})
    ledger.append(run)
    ledger.append(other)
    found = ledger.get("abc")
    assert found is not None
    assert found.id == "abc123"
    report = compare_runs([run, other])
    assert len(report.rows) == 2
    assert report.rows[0].gate_outcome == "warn"
