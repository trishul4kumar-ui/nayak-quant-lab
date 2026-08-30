from __future__ import annotations

from datetime import UTC, datetime

import pytest

from quantlab.core.identifiers import InstrumentId
from quantlab.core.time import PointInTime
from quantlab.domain.models import OHLCVBar
from quantlab.domain.research import CheckResult
from quantlab.research.integrity import evaluate_integrity


def _bar(day: datetime) -> OHLCVBar:
    pit = PointInTime(event_time=day, effective_time=day, available_time=day, ingestion_time=day)
    return OHLCVBar(
        instrument=InstrumentId.parse("NSE:TEST"),
        pit=pit,
        open=1.0,
        high=1.0,
        low=1.0,
        close=1.0,
    )


@pytest.mark.discovery
def test_discovery_leak_flags_fail() -> None:
    day = datetime(2024, 1, 2, tzinfo=UTC)
    report = evaluate_integrity(
        bars=[_bar(day)],
        states=[],
        as_of_times=[day],
        next_bar_fill=True,
        cost_bps=10.0,
        slippage_model="none",
        live_trading=False,
        n_experiments_in_family=4,
        used_ml=False,
        hidden_candidate=True,
        posthoc_search_budget=True,
        future_fitness=True,
        label_used_as_feature=True,
    )
    assert report.checks["hidden_candidate"] is CheckResult.FAIL
    assert report.checks["posthoc_search_budget"] is CheckResult.FAIL
    assert report.checks["future_fitness"] is CheckResult.FAIL
    assert report.checks["label_as_feature"] is CheckResult.FAIL
    assert report.failed()
