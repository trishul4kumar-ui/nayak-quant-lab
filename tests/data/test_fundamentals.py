from datetime import UTC, date, datetime, timedelta

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
