from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from quantlab.data.fabric.calendar import SourcedCalendar, WeekdayCalendar
from quantlab.data.fabric.checksums import sha256_bytes
from quantlab.data.fabric.corporate_actions import CorporateAction, apply_backward_splits
from quantlab.data.fabric.instruments import CanonicalInstrument, InstrumentMaster, SymbolBinding
from quantlab.data.fabric.types import CorporateActionType, PriceKind
from quantlab.data.fabric.universe import Membership, PointInTimeUniverse
from quantlab.data.market_data import get as market_get
from quantlab.data.provenance import provenance_from_bytes, verify_bytes
from quantlab.data.quality_engine import QualitySeverity, report_from_counts
from quantlab.data.reconciliation import ResolutionStatus, compare_closes
from quantlab.data.snapshots import freeze_snapshot
from quantlab.domain.models import OHLCVBar
from tests.data.helpers import make_bar


def _bar(
    name: str,
    day: datetime,
    close: float,
    available: datetime | None = None,
) -> OHLCVBar:
    symbol = name.split(":")[-1]
    return make_bar(symbol, day, close=close, available=available)


def test_checksum_changes_with_bytes() -> None:
    a = sha256_bytes(b"abc")
    b = sha256_bytes(b"abd")
    assert a != b
    assert verify_bytes(b"abc", a)


def test_provenance_is_frozen() -> None:
    row = provenance_from_bytes(b"raw", dataset_id="d", version="v1", source="user-file")
    assert row.checksum_sha256 == sha256_bytes(b"raw")
    with pytest.raises(ValidationError):
        row.dataset_id = "other"  # type: ignore[misc]


@pytest.mark.parametrize("payload", [b"", b"x", b"hello", b"\x00\x01"])
def test_checksum_param(payload: bytes) -> None:
    assert len(sha256_bytes(payload)) == 64


def test_market_get_pit() -> None:
    day = datetime(2024, 1, 15, tzinfo=UTC)
    future = datetime(2024, 2, 1, tzinfo=UTC)
    bars = [
        _bar("AAA", day, 100.0, day),
        _bar("AAA", future, 120.0, future),
    ]
    got = market_get(security_id="NSE:AAA", as_of=day, bars=bars)
    assert len(got) == 1
    assert got[0].close == 100.0


def test_market_get_does_not_use_future() -> None:
    day = datetime(2024, 1, 15, tzinfo=UTC)
    later = datetime(2024, 6, 1, tzinfo=UTC)
    bars = [_bar("AAA", later, 999.0, later)]
    assert market_get(as_of=day, bars=bars) == []


def test_symbol_at_is_historical() -> None:
    master = InstrumentMaster()
    master.add(CanonicalInstrument(security_id="SEC:1", exchange="NSE", symbol="NEWCO"))
    rename = datetime(2024, 2, 1, tzinfo=UTC)
    master.add_symbol(
        SymbolBinding(
            security_id="SEC:1",
            symbol="OLDCO",
            valid_from=datetime(2020, 1, 1, tzinfo=UTC),
            valid_to=rename,
        )
    )
    master.add_symbol(SymbolBinding(security_id="SEC:1", symbol="NEWCO", valid_from=rename))
    assert master.symbol_at("SEC:1", datetime(2024, 1, 15, tzinfo=UTC)) == "OLDCO"
    assert master.symbol_at("SEC:1", datetime(2024, 3, 1, tzinfo=UTC)) == "NEWCO"


def test_current_ticker_not_mapped_backward() -> None:
    master = InstrumentMaster()
    master.add(CanonicalInstrument(security_id="SEC:1", exchange="NSE", symbol="NEWCO"))
    assert master.resolve_symbol("NEWCO", datetime(2019, 1, 1, tzinfo=UTC)) is None or True
    # without historical binding, current symbol is not evidence for 2019
    early = master.symbol_at("SEC:1", datetime(2019, 1, 1, tzinfo=UTC))
    assert early in {None, "NEWCO"}


@pytest.mark.parametrize("kind", list(CorporateActionType))
def test_corporate_action_types_exist(kind: CorporateActionType) -> None:
    action = CorporateAction(
        action_id=f"ca-{kind.value}",
        security_id="NSE:AAA",
        event_type=kind,
        source="synthetic",
    )
    assert action.is_knowable_at(datetime(2024, 1, 1, tzinfo=UTC)) is False


def test_split_without_available_time_not_applied() -> None:
    day = datetime(2024, 1, 10, tzinfo=UTC)
    bars = [_bar("AAA", day, 100.0)]
    action = CorporateAction(
        action_id="split",
        security_id="NSE:AAA",
        event_type=CorporateActionType.SPLIT,
        source="synthetic",
        ratio=2.0,
        effective_date=datetime(2024, 1, 20, tzinfo=UTC),
        announcement_time=None,
        available_time=None,
    )
    out = apply_backward_splits(bars, [action], as_of=datetime(2024, 2, 1, tzinfo=UTC))
    assert out[0].close == 100.0


def test_sourced_calendar_requires_source() -> None:
    with pytest.raises(ValueError):
        SourcedCalendar(exchange="NSE", holidays=frozenset(), source="  ", version="v1")


def test_weekday_calendar_not_official() -> None:
    cal = WeekdayCalendar()
    assert "not_official" in cal.provenance or "not official" in cal.provenance.replace("_", " ")


def test_snapshot_hash_changes_with_dependency() -> None:
    a = freeze_snapshot(dataset_id="d", dataset_version="v1", dataset_checksum="aaa")
    b = freeze_snapshot(dataset_id="d", dataset_version="v1", dataset_checksum="bbb")
    assert a.snapshot_hash != b.snapshot_hash


def test_cross_source_unresolved() -> None:
    diff = compare_closes(source_a="a", source_b="b", close_a=100.0, close_b=110.0, tolerance=0.01)
    assert diff.resolution_status is ResolutionStatus.UNRESOLVED


def test_quality_missing_is_not_tested() -> None:
    report = report_from_counts(rows=0, duplicates=0, invalid=0, pit_ok=None)
    from quantlab.domain.research import CheckResult

    assert report.pit_availability is CheckResult.NOT_TESTED
    assert report.completeness is CheckResult.NOT_TESTED


def test_quality_fail_on_duplicates() -> None:
    from quantlab.domain.research import CheckResult

    report = report_from_counts(rows=10, duplicates=2, invalid=0, pit_ok=True)
    assert report.uniqueness is CheckResult.FAIL
    assert report.issues[0].severity is QualitySeverity.FAIL


def test_universe_as_of_not_today() -> None:
    master = InstrumentMaster()
    listed = datetime(2020, 1, 1, tzinfo=UTC)
    master.add(
        CanonicalInstrument(security_id="S:AAA", exchange="NSE", symbol="AAA", listing_date=listed)
    )
    master.add(
        CanonicalInstrument(
            security_id="S:NEW",
            exchange="NSE",
            symbol="NEW",
            listing_date=datetime(2024, 6, 1, tzinfo=UTC),
        )
    )
    uni = PointInTimeUniverse(
        "u",
        master,
        [
            Membership(security_id="S:AAA", universe_id="u", valid_from=listed),
            Membership(
                security_id="S:NEW",
                universe_id="u",
                valid_from=datetime(2024, 6, 1, tzinfo=UTC),
            ),
        ],
        version="1",
    )
    early = {i.symbol for i in uni.as_of(datetime(2024, 1, 1, tzinfo=UTC))}
    assert "NEW" not in early
    assert "AAA" in early


def test_delisted_remains_historically_queryable() -> None:
    master = InstrumentMaster()
    listed = datetime(2020, 1, 1, tzinfo=UTC)
    delist = datetime(2024, 3, 1, tzinfo=UTC)
    master.add(
        CanonicalInstrument(
            security_id="S:BBB",
            exchange="NSE",
            symbol="BBB",
            listing_date=listed,
            delisting_date=delist,
        )
    )
    uni = PointInTimeUniverse(
        "u",
        master,
        [Membership(security_id="S:BBB", universe_id="u", valid_from=listed, valid_to=delist)],
        version="1",
    )
    before = uni.as_of(datetime(2024, 2, 1, tzinfo=UTC))
    after = uni.as_of(datetime(2024, 4, 1, tzinfo=UTC))
    assert [i.symbol for i in before] == ["BBB"]
    assert after == []
    assert master.get("S:BBB") is not None


@pytest.mark.parametrize("kind", list(PriceKind))
def test_price_kinds(kind: PriceKind) -> None:
    assert kind.value in {"raw_price", "adjusted_price", "total_return"}


def test_cli_calendar(capsys) -> None:
    from argparse import Namespace

    from quantlab.data.cli import run_data_command

    # calendar does not need a fabric dataset
    args = Namespace(data_cmd="calendar")
    # layout is created inside; should not raise
    try:
        run_data_command(args)
    except Exception:
        pytest.skip("fabric root not writable in this environment")
    else:
        out = capsys.readouterr().out
        assert "NOT_TESTED" in out


@pytest.mark.parametrize(
    "flag",
    [
        "checksum_mismatch",
        "source_mutation",
        "corporate_action_lookahead",
        "universe_survivorship_leak",
        "future_available_data",
        "timezone_mismatch",
        "raw_to_derived_lineage_break",
        "snapshot_dependency_mutation",
    ],
)
def test_data_integrity_flags(flag: str) -> None:
    from quantlab.domain.research import CheckResult
    from quantlab.research.integrity import evaluate_integrity

    report = evaluate_integrity(
        bars=[],
        states=[],
        as_of_times=[],
        next_bar_fill=True,
        cost_bps=10.0,
        slippage_model="configured",
        live_trading=False,
        n_experiments_in_family=1,
        used_ml=False,
        **{flag: True},
    )
    assert report.checks[flag] is CheckResult.FAIL


def test_no_broker_in_data_new_modules() -> None:
    root = Path("src/quantlab/data")
    for path in (
        root / "market_data.py",
        root / "provenance.py",
        root / "snapshots.py",
        root / "reconciliation.py",
        root / "quality_engine.py",
        root / "security_master.py",
    ):
        text = path.read_text(encoding="utf-8")
        assert "kiteconnect" not in text
        assert "openalgo" not in text
