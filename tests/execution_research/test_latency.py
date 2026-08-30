from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from quantlab.core.errors import ExecutionResearchError
from quantlab.domain.models import Side
from quantlab.execution_research.definition import OrderIntent
from quantlab.execution_research.fills import simulate_fill
from quantlab.execution_research.latency import arrival_index
from quantlab.execution_research.registry import get_execution_model


def test_latency_does_not_fill_before_arrival() -> None:
    model = get_execution_model("exec_high_latency")
    idx = arrival_index(model, decision_index=10, n_sessions=40)
    assert idx == 12


def test_fill_before_decision_raises() -> None:
    as_of = datetime(2024, 1, 3, tzinfo=UTC)
    intent = OrderIntent(
        intent_id="late",
        decision_time=as_of,
        security_id="NSE:TCS",
        side=Side.BUY,
        target_quantity=10.0,
        reference_price=100.0,
        max_participation=1.0,
    )
    with pytest.raises(ExecutionResearchError):
        simulate_fill(
            intent,
            get_execution_model("exec_base"),
            arrival_time=as_of - timedelta(days=1),
            arrival_price=100.0,
            volume=1_000_000.0,
            trailing_volume=1_000_000.0,
            trailing_vol=0.01,
        )
