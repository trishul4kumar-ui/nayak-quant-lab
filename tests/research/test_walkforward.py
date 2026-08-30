from datetime import UTC, datetime, timedelta

from quantlab.research.splits import apply_embargo, assert_temporally_ordered, purge_train_times
from quantlab.research.walkforward import WindowKind, generate_walk_forward


def _calendar(n: int = 80) -> list[datetime]:
    start = datetime(2024, 1, 2, tzinfo=UTC)
    return [start + timedelta(days=i) for i in range(n)]


def test_expanding_windows_are_ordered() -> None:
    plan = generate_walk_forward(
        _calendar(),
        train_sessions=30,
        test_sessions=8,
        step_sessions=8,
        kind=WindowKind.EXPANDING,
        embargo_sessions=1,
        label_horizon_sessions=1,
    )
    assert plan.windows
    previous = None
    for window in plan.windows:
        assert window.train_end < window.test_start
        assert window.test_end >= window.test_start
        if previous is not None:
            assert window.train_end >= previous.train_end
        previous = window


def test_rolling_windows_move_train_start() -> None:
    plan = generate_walk_forward(
        _calendar(),
        train_sessions=20,
        test_sessions=5,
        step_sessions=8,
        kind=WindowKind.ROLLING,
        embargo_sessions=0,
        label_horizon_sessions=1,
    )
    assert len(plan.windows) >= 2
    assert plan.windows[0].train_start < plan.windows[1].train_start


def test_embargo_skips_sessions() -> None:
    cal = _calendar(10)
    got = apply_embargo(cal[2], cal, 1)
    assert got == cal[4]


def test_purge_drops_overlapping_labels() -> None:
    cal = _calendar(10)
    train = cal[:5]
    purged = purge_train_times(train, cal[5], cal, label_horizon_sessions=1)
    assert cal[4] not in purged
    assert cal[3] in purged


def test_temporally_ordered_windows() -> None:
    cal = _calendar(6)
    assert assert_temporally_ordered([(cal[0], cal[2]), (cal[2], cal[5])]) is True
    assert assert_temporally_ordered([(cal[0], cal[3]), (cal[2], cal[5])]) is False
