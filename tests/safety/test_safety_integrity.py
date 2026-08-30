from __future__ import annotations

from datetime import UTC, datetime

from quantlab.core.identifiers import InstrumentId
from quantlab.core.time import PointInTime
from quantlab.domain.models import OHLCVBar
from quantlab.domain.research import CheckResult
from quantlab.research.integrity import evaluate_integrity
from quantlab.safety.models import SafetyRequest
from quantlab.safety.service import evaluate_request


def _bar() -> OHLCVBar:
    day = datetime(2024, 1, 2, tzinfo=UTC)
    pit = PointInTime(event_time=day, effective_time=day, available_time=day, ingestion_time=day)
    return OHLCVBar(
        instrument=InstrumentId.parse("NSE:TCS"),
        pit=pit,
        open=10,
        high=11,
        low=9,
        close=10,
    )


def test_integrity_flags_from_incidents() -> None:
    day = datetime(2024, 1, 2, tzinfo=UTC)
    result = evaluate_request(SafetyRequest(ai_override=True))
    report = evaluate_integrity(
        bars=[_bar()],
        states=[],
        as_of_times=[day],
        next_bar_fill=True,
        cost_bps=10.0,
        slippage_model="none",
        live_trading=result.live_trading,
        n_experiments_in_family=1,
        used_ml=False,
        ai_safety_override=True,
        unauthorized_release=True,
    )
    assert report.checks["ai_safety_override"] is CheckResult.FAIL
    assert report.checks["unauthorized_release"] is CheckResult.FAIL
