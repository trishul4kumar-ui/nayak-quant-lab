from datetime import UTC, date, datetime, timedelta

import pytest

from quantlab.core.errors import DataIntegrityError
from quantlab.data.fabric.fundamentals import FundamentalObservation, FundamentalStore


def test_fundamental_revision_as_of() -> None:
    store = FundamentalStore()
    t1 = datetime(2024, 4, 15, 12, 0, tzinfo=UTC)
    t2 = datetime(2024, 5, 20, 12, 0, tzinfo=UTC)
    store.add(
        FundamentalObservation(
            security_id="SYNTH:NSE:TCS",
            metric="net_income",
            value=10.0,
            period_start=date(2023, 10, 1),
            period_end=date(2023, 12, 31),
            publication_time=t1,
            available_time=t1,
            source="synthetic_fixture",
            revision=1,
        )
    )
    store.add(
        FundamentalObservation(
            security_id="SYNTH:NSE:TCS",
            metric="net_income",
            value=12.0,
            period_start=date(2023, 10, 1),
            period_end=date(2023, 12, 31),
            publication_time=t2,
            available_time=t2,
            source="synthetic_fixture",
            revision=2,
        )
    )
    assert store.as_of("SYNTH:NSE:TCS", "net_income", t1 - timedelta(days=1)) is None
    first = store.as_of("SYNTH:NSE:TCS", "net_income", t1)
    second = store.as_of("SYNTH:NSE:TCS", "net_income", t2)
    assert first is not None and first.value == 10.0 and first.revision == 1
    assert second is not None and second.value == 12.0 and second.revision == 2


def test_older_period_revision_does_not_replace_newer_period() -> None:
    store = FundamentalStore()
    initial = FundamentalObservation(
        security_id="SYNTH:NSE:TCS",
        metric="revenue",
        value=10.0,
        period_start=date(2023, 10, 1),
        period_end=date(2023, 12, 31),
        publication_time=datetime(2024, 2, 1, tzinfo=UTC),
        available_time=datetime(2024, 2, 1, tzinfo=UTC),
        source="synthetic_fixture",
    )
    newer = initial.model_copy(
        update={
            "period_start": date(2024, 1, 1),
            "period_end": date(2024, 3, 31),
            "value": 20.0,
            "publication_time": datetime(2024, 4, 1, tzinfo=UTC),
            "available_time": datetime(2024, 4, 1, tzinfo=UTC),
        }
    )
    correction = initial.model_copy(
        update={
            "value": 11.0,
            "revision": 2,
            "publication_time": datetime(2024, 5, 1, tzinfo=UTC),
            "available_time": datetime(2024, 5, 1, tzinfo=UTC),
        }
    )
    for item in (initial, newer, correction):
        store.add(item)
    result = store.as_of(initial.security_id, initial.metric, datetime(2024, 5, 2, tzinfo=UTC))
    assert result is not None and result.value == 20.0
    result.value = 99.0
    assert (
        store.as_of(initial.security_id, initial.metric, datetime(2024, 5, 2, tzinfo=UTC)).value
        == 20.0
    )
    with pytest.raises(DataIntegrityError, match="conflicting"):
        store.add(correction.model_copy(update={"value": 50.0}))
