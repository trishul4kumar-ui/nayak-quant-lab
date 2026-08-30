from datetime import UTC, datetime, timedelta

from quantlab.data.fabric.corporate_actions import CorporateAction, apply_backward_splits
from quantlab.data.fabric.types import CorporateActionType
from tests.data.helpers import make_bar, utc_day


def test_split_not_applied_before_available_time() -> None:
    t0 = utc_day(2024, 1, 2)
    t1 = utc_day(2024, 1, 3)
    t2 = utc_day(2024, 1, 4)
    bars = [
        make_bar("TCS", t0, close=100.0),
        make_bar("TCS", t1, close=100.0),
        make_bar("TCS", t2, close=50.0),
    ]
    action = CorporateAction(
        action_id="split-1",
        security_id="NSE:TCS",
        event_type=CorporateActionType.SPLIT,
        source="synthetic_fixture",
        announcement_time=t1,
        effective_date=t2,
        available_time=t1,
        ratio=2.0,
    )
    before = apply_backward_splits(bars, [action], as_of=t0)
    assert [b.close for b in before] == [100.0, 100.0, 50.0]
    after = apply_backward_splits(bars, [action], as_of=t1)
    assert after[0].close == 50.0
    assert after[1].close == 50.0
    assert after[2].close == 50.0
    assert after[0].price_kind == "adjusted_price"


def test_missing_announcement_is_unknowable() -> None:
    t0 = utc_day(2024, 1, 2)
    action = CorporateAction(
        action_id="split-unknown",
        security_id="NSE:TCS",
        event_type=CorporateActionType.SPLIT,
        source="synthetic_fixture",
        announcement_time=None,
        available_time=None,
        effective_date=t0 + timedelta(days=1),
        ratio=2.0,
    )
    assert action.is_knowable_at(datetime.now(tz=UTC)) is False
    bars = [make_bar("TCS", t0, close=100.0)]
    out = apply_backward_splits(bars, [action], as_of=datetime.now(tz=UTC))
    assert out[0].close == 100.0
