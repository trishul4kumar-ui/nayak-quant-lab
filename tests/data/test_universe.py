from datetime import UTC, datetime

from quantlab.data.fabric.instruments import CanonicalInstrument, InstrumentMaster, SymbolBinding
from quantlab.data.fabric.universe import Membership, PointInTimeUniverse


def test_universe_as_of_excludes_delisted_and_future_members() -> None:
    master = InstrumentMaster()
    listed = datetime(2020, 1, 1, tzinfo=UTC)
    delist = datetime(2024, 3, 1, tzinfo=UTC)
    master.add(
        CanonicalInstrument(
            security_id="SYNTH:NSE:AAA",
            exchange="NSE",
            symbol="AAA",
            listing_date=listed,
        )
    )
    master.add(
        CanonicalInstrument(
            security_id="SYNTH:NSE:BBB",
            exchange="NSE",
            symbol="BBB",
            listing_date=listed,
            delisting_date=delist,
        )
    )
    master.add(
        CanonicalInstrument(
            security_id="SYNTH:NSE:NEW",
            exchange="NSE",
            symbol="NEW",
            listing_date=datetime(2024, 6, 1, tzinfo=UTC),
        )
    )
    memberships = [
        Membership(
            security_id="SYNTH:NSE:AAA",
            universe_id="synth-index",
            valid_from=listed,
        ),
        Membership(
            security_id="SYNTH:NSE:BBB",
            universe_id="synth-index",
            valid_from=listed,
            valid_to=delist,
        ),
        Membership(
            security_id="SYNTH:NSE:NEW",
            universe_id="synth-index",
            valid_from=datetime(2024, 6, 1, tzinfo=UTC),
        ),
    ]
    universe = PointInTimeUniverse("synth-index", master, memberships, version="u-v1")
    before_delist = universe.as_of(datetime(2024, 2, 1, tzinfo=UTC))
    after_delist = universe.as_of(datetime(2024, 4, 1, tzinfo=UTC))
    today_like = universe.as_of(datetime(2024, 7, 1, tzinfo=UTC))
    assert {i.symbol for i in before_delist} == {"AAA", "BBB"}
    assert {i.symbol for i in after_delist} == {"AAA"}
    assert {i.symbol for i in today_like} == {"AAA", "NEW"}
    assert "BBB" not in {i.symbol for i in today_like}


def test_symbol_history_is_as_of() -> None:
    master = InstrumentMaster()
    master.add(
        CanonicalInstrument(
            security_id="SYNTH:NSE:OLDCO",
            exchange="NSE",
            symbol="NEWCO",
        )
    )
    rename = datetime(2024, 2, 1, tzinfo=UTC)
    master.add_symbol(
        SymbolBinding(
            security_id="SYNTH:NSE:OLDCO",
            symbol="OLDCO",
            valid_from=datetime(2020, 1, 1, tzinfo=UTC),
            valid_to=rename,
        )
    )
    master.add_symbol(
        SymbolBinding(
            security_id="SYNTH:NSE:OLDCO",
            symbol="NEWCO",
            valid_from=rename,
        )
    )
    early = master.resolve_symbol("OLDCO", datetime(2024, 1, 15, tzinfo=UTC))
    late = master.resolve_symbol("NEWCO", datetime(2024, 3, 1, tzinfo=UTC))
    gone = master.resolve_symbol("OLDCO", datetime(2024, 3, 1, tzinfo=UTC))
    assert early is not None and early.security_id == "SYNTH:NSE:OLDCO"
    assert late is not None and late.security_id == "SYNTH:NSE:OLDCO"
    assert gone is None
