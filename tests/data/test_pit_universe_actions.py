from datetime import UTC, datetime, timedelta

import pytest

from quantlab.core.errors import DataIntegrityError
from quantlab.data.fabric.corporate_actions import CorporateAction, apply_backward_splits
from quantlab.data.fabric.instruments import CanonicalInstrument, InstrumentMaster
from quantlab.data.fabric.types import CorporateActionType
from quantlab.data.fabric.universe import Membership, PointInTimeUniverse
from tests.data.helpers import make_bar


def _dt(day: int) -> datetime:
    return datetime(2024, 1, day, tzinfo=UTC)


def _universe(rows: list[Membership]) -> PointInTimeUniverse:
    master = InstrumentMaster()
    inst = CanonicalInstrument(
        security_id="NSE:AAA", exchange="NSE", symbol="AAA", listing_date=_dt(1)
    )
    master.add(inst)
    master.add_pit_revision(inst, effective_time=_dt(1), available_time=_dt(1), source="fixture")
    return PointInTimeUniverse("index-a", master, rows, version="fixture-v1")


def _membership(**updates: object) -> Membership:
    values: dict[str, object] = {
        "membership_id": "a-1",
        "security_id": "NSE:AAA",
        "universe_id": "index-a",
        "valid_from": _dt(1),
        "available_time": _dt(1),
        "source": "synthetic_fixture",
    }
    values.update(updates)
    return Membership.model_validate(values)


def test_membership_revision_is_used_only_after_its_availability() -> None:
    original = _membership()
    correction = _membership(valid_to=_dt(4), available_time=_dt(8))
    universe = _universe([correction, original])
    assert [row.security_id for row in universe.as_of(_dt(6))] == ["NSE:AAA"]
    assert universe.as_of(_dt(8)) == []
    assert [row.security_id for row in universe.as_of(_dt(2))] == ["NSE:AAA"]


def test_foreign_universe_and_future_membership_do_not_leak() -> None:
    foreign = _membership(membership_id="a-2", universe_id="index-b")
    late = _membership(available_time=_dt(8))
    assert _universe([foreign, late]).as_of(_dt(5)) == []


@pytest.mark.parametrize("updates", [
    {"available_time": None}, {"source": ""}, {"membership_id": ""},
    {"valid_to": _dt(1)}, {"available_time": datetime(2024, 1, 1)},
])
def test_missing_or_invalid_membership_evidence_fails_closed(updates: dict[str, object]) -> None:
    with pytest.raises(DataIntegrityError):
        _universe([_membership(**updates)]).as_of(_dt(5))


def test_same_timestamp_conflicting_membership_revisions_fail_closed() -> None:
    with pytest.raises(DataIntegrityError, match="conflicting"):
        _universe([_membership(), _membership(valid_to=_dt(4))]).as_of(_dt(5))


def test_overlapping_membership_events_fail_closed() -> None:
    with pytest.raises(DataIntegrityError, match="overlapping"):
        _universe([_membership(), _membership(membership_id="a-2")]).as_of(_dt(5))


def test_universe_refuses_master_data_without_a_known_pit_revision() -> None:
    master = InstrumentMaster()
    master.add(CanonicalInstrument(
        security_id="NSE:AAA", exchange="NSE", symbol="TODAY", listing_date=_dt(1)
    ))
    universe = PointInTimeUniverse("index-a", master, [_membership()], version="v1")
    with pytest.raises(DataIntegrityError, match="point-in-time security-master"):
        universe.as_of(_dt(5))


def test_master_revision_uses_only_labels_and_delisting_known_by_cutoff() -> None:
    master = InstrumentMaster()
    original = CanonicalInstrument(
        security_id="NSE:AAA", exchange="NSE", symbol="OLD", listing_date=_dt(1)
    )
    later = original.model_copy(update={"symbol": "NEW", "delisting_date": _dt(7)})
    master.add_pit_revision(
        original, effective_time=_dt(1), available_time=_dt(1), source="fixture"
    )
    # The correction refers to an already-effective date but was learned later.
    master.add_pit_revision(later, effective_time=_dt(1), available_time=_dt(8), source="fixture")
    universe = PointInTimeUniverse("index-a", master, [_membership()], version="v1")
    assert [row.symbol for row in universe.as_of(_dt(6))] == ["OLD"]
    assert universe.as_of(_dt(8)) == []
    original.symbol = "MUTATED"
    assert master.get_as_of("NSE:AAA", _dt(6)).symbol == "OLD"  # type: ignore[union-attr]


def test_conflicting_master_revision_is_not_silently_overwritten() -> None:
    master = InstrumentMaster()
    original = CanonicalInstrument(
        security_id="NSE:AAA", exchange="NSE", symbol="AAA", listing_date=_dt(1)
    )
    master.add_pit_revision(
        original, effective_time=_dt(1), available_time=_dt(1), source="fixture"
    )
    changed = original.model_copy(update={"symbol": "OTHER"})
    with pytest.raises(DataIntegrityError, match="conflicting"):
        master.add_pit_revision(
            changed, effective_time=_dt(1), available_time=_dt(1), source="fixture"
        )


def _split(**updates: object) -> CorporateAction:
    values: dict[str, object] = {
        "action_id": "split-1", "security_id": "NSE:AAA",
        "event_type": CorporateActionType.SPLIT, "source": "synthetic_fixture",
        "announcement_time": _dt(2), "available_time": _dt(2),
        "effective_date": _dt(4), "ratio": 2.0,
    }
    values.update(updates)
    return CorporateAction.model_validate(values)


def test_split_revision_only_replaces_old_ratio_when_known() -> None:
    bar = make_bar("AAA", _dt(1), close=120.0)
    correction = _split(available_time=_dt(8), ratio=3.0)
    assert apply_backward_splits([bar], [_split(), correction], as_of=_dt(5))[0].close == 60.0
    assert apply_backward_splits([bar], [_split(), correction], as_of=_dt(8))[0].close == 40.0


def test_future_bar_or_availability_fails_closed() -> None:
    cutoff = _dt(5)
    with pytest.raises(DataIntegrityError, match="event time"):
        apply_backward_splits([make_bar("AAA", _dt(6))], [], as_of=cutoff)
    with pytest.raises(DataIntegrityError, match="bar availability"):
        apply_backward_splits([make_bar("AAA", _dt(4), available=_dt(6))], [], as_of=cutoff)


def test_split_ratio_must_be_finite() -> None:
    with pytest.raises(ValueError, match="positive ratio"):
        apply_backward_splits([make_bar("AAA", _dt(1))], [_split(ratio=float("nan"))], as_of=_dt(5))


def test_conflicting_action_revisions_and_missing_effective_time_fail() -> None:
    bar = make_bar("AAA", _dt(1))
    with pytest.raises(DataIntegrityError, match="conflicting"):
        apply_backward_splits([bar], [_split(), _split(ratio=3.0)], as_of=_dt(5))
    with pytest.raises(DataIntegrityError, match="effective"):
        apply_backward_splits([bar], [_split(effective_date=None)], as_of=_dt(5))


def test_future_action_is_not_applied() -> None:
    bar = make_bar("AAA", _dt(1))
    action = _split(available_time=_dt(5) + timedelta(hours=1))
    assert apply_backward_splits([bar], [action], as_of=_dt(5))[0].close == 100.0
