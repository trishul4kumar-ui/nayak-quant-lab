from __future__ import annotations

from pathlib import Path

import pytest

from quantlab.digital_twin.integrity import report_from_twin
from quantlab.digital_twin.service import run_twin
from quantlab.domain.research import CheckResult
from quantlab.realtime_data.integrity import report_from_snapshot
from quantlab.realtime_data.mock import SEED_AS_OF
from quantlab.realtime_data.service import snapshot, start
from quantlab.realtime_decision.integrity import report_from_decision
from quantlab.realtime_decision.models import synthetic_research_release
from quantlab.realtime_decision.service import run_realtime_decision

pytestmark = pytest.mark.realtime_data


def test_realtime_integrity_does_not_hide_future() -> None:
    start()
    report = report_from_snapshot(snapshot())
    assert report.checks["future_market_observation"] is CheckResult.PASS
    assert report.checks["realtime_snapshot_mutation"] is CheckResult.PASS


def test_decision_integrity() -> None:
    item = run_realtime_decision(release=synthetic_research_release(as_of=SEED_AS_OF))
    report = report_from_decision(item)
    assert report.checks["ai_authority_violation"] is CheckResult.PASS
    assert item.live_trading is False


def test_twin_integrity() -> None:
    item = run_twin()
    report = report_from_twin(item)
    assert report.checks["shadow_routing_attempt"] is CheckResult.PASS
    assert report.checks["simulated_fill_as_broker_fill"] is CheckResult.PASS


def test_packages_do_not_import_brokers() -> None:
    for folder in (
        "src/quantlab/realtime_data",
        "src/quantlab/realtime_decision",
        "src/quantlab/digital_twin",
    ):
        blob = "\n".join(path.read_text() for path in Path(folder).glob("*.py"))
        assert "kiteconnect" not in blob
        assert "from quantlab.brokers" not in blob
