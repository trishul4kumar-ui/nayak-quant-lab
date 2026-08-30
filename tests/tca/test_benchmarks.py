from __future__ import annotations

from datetime import UTC, datetime

import pytest

from quantlab.domain.models import Side
from quantlab.paper_oms.models import PaperFill
from quantlab.tca.enums import ArrivalPolicy
from quantlab.tca.shortfall import arrival_price


def _fill() -> PaperFill:
    return PaperFill(
        fill_id="F",
        order_id="O",
        security_id="NSE:AAA",
        side=Side.BUY,
        requested_quantity=1.0,
        filled_quantity=1.0,
        remaining_quantity=0.0,
        reference_price=100.0,
        arrival_price=101.0,
        execution_price=102.0,
        gross_notional=102.0,
        arrival_time=datetime(2024, 1, 15, tzinfo=UTC),
        fill_time=datetime(2024, 1, 15, tzinfo=UTC),
        execution_model_id="base",
    )


@pytest.mark.parametrize("policy", list(ArrivalPolicy))
def test_arrival_policies(policy: ArrivalPolicy) -> None:
    fill = _fill()
    price = arrival_price(fill, policy, user=99.0)
    if policy is ArrivalPolicy.UNAVAILABLE:
        assert price is None
    elif policy is ArrivalPolicy.USER_SUPPLIED:
        assert price == 99.0
    elif policy is ArrivalPolicy.BAR_DERIVED:
        assert price == 100.0
    else:
        assert price == 101.0
