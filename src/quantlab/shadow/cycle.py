"""Shadow mode and cycle state machines. Illegal transitions fail closed."""

from __future__ import annotations

from quantlab.core.errors import InvalidShadowTransition
from quantlab.shadow.enums import CycleStatus, ShadowMode, ShadowOrderStatus

_MODE: dict[ShadowMode, frozenset[ShadowMode]] = {
    ShadowMode.OFF: frozenset(
        {ShadowMode.RESEARCH_PAPER, ShadowMode.PAPER, ShadowMode.SHADOW}
    ),
    ShadowMode.RESEARCH_PAPER: frozenset(
        {ShadowMode.PAUSED, ShadowMode.HALTED, ShadowMode.OFF, ShadowMode.ERROR}
    ),
    ShadowMode.PAPER: frozenset(
        {
            ShadowMode.PAUSED,
            ShadowMode.HALTED,
            ShadowMode.SHADOW,
            ShadowMode.OFF,
            ShadowMode.ERROR,
        }
    ),
    ShadowMode.SHADOW: frozenset(
        {
            ShadowMode.PAUSED,
            ShadowMode.HALTED,
            ShadowMode.PAPER,
            ShadowMode.OFF,
            ShadowMode.ERROR,
        }
    ),
    ShadowMode.PAUSED: frozenset(
        {
            ShadowMode.RESEARCH_PAPER,
            ShadowMode.PAPER,
            ShadowMode.SHADOW,
            ShadowMode.HALTED,
            ShadowMode.OFF,
        }
    ),
    ShadowMode.HALTED: frozenset({ShadowMode.RECOVERY, ShadowMode.OFF}),
    ShadowMode.ERROR: frozenset(
        {ShadowMode.RECOVERY, ShadowMode.HALTED, ShadowMode.OFF}
    ),
    ShadowMode.RECOVERY: frozenset(
        {
            ShadowMode.RESEARCH_PAPER,
            ShadowMode.PAPER,
            ShadowMode.SHADOW,
            ShadowMode.HALTED,
            ShadowMode.OFF,
        }
    ),
}

_CYCLE: dict[CycleStatus, frozenset[CycleStatus]] = {
    CycleStatus.CREATED: frozenset(
        {
            CycleStatus.VALIDATED,
            CycleStatus.ABSTAINED,
            CycleStatus.REJECTED,
            CycleStatus.FAILED,
            CycleStatus.HALTED,
        }
    ),
    CycleStatus.VALIDATED: frozenset(
        {
            CycleStatus.SNAPSHOT_FROZEN,
            CycleStatus.ABSTAINED,
            CycleStatus.REJECTED,
            CycleStatus.FAILED,
            CycleStatus.HALTED,
        }
    ),
    CycleStatus.SNAPSHOT_FROZEN: frozenset(
        {
            CycleStatus.EXECUTED,
            CycleStatus.ABSTAINED,
            CycleStatus.REJECTED,
            CycleStatus.FAILED,
            CycleStatus.HALTED,
        }
    ),
    CycleStatus.EXECUTED: frozenset(
        {CycleStatus.RECONCILED, CycleStatus.FAILED, CycleStatus.HALTED}
    ),
    CycleStatus.RECONCILED: frozenset(
        {CycleStatus.COMPLETED, CycleStatus.FAILED, CycleStatus.HALTED}
    ),
    CycleStatus.COMPLETED: frozenset(),
    CycleStatus.ABSTAINED: frozenset(),
    CycleStatus.REJECTED: frozenset(),
    CycleStatus.FAILED: frozenset(),
    CycleStatus.HALTED: frozenset(),
}

_ORDER: dict[ShadowOrderStatus, frozenset[ShadowOrderStatus]] = {
    ShadowOrderStatus.CREATED: frozenset(
        {ShadowOrderStatus.VALIDATED, ShadowOrderStatus.REJECTED, ShadowOrderStatus.ABSTAINED}
    ),
    ShadowOrderStatus.VALIDATED: frozenset(
        {ShadowOrderStatus.SIMULATED, ShadowOrderStatus.REJECTED, ShadowOrderStatus.ABSTAINED}
    ),
    ShadowOrderStatus.SIMULATED: frozenset(
        {ShadowOrderStatus.PARTIAL, ShadowOrderStatus.COMPLETED, ShadowOrderStatus.REJECTED}
    ),
    ShadowOrderStatus.PARTIAL: frozenset(
        {ShadowOrderStatus.COMPLETED, ShadowOrderStatus.REJECTED}
    ),
    ShadowOrderStatus.COMPLETED: frozenset({ShadowOrderStatus.RECONCILED}),
    ShadowOrderStatus.RECONCILED: frozenset(),
    ShadowOrderStatus.ABSTAINED: frozenset(),
    ShadowOrderStatus.REJECTED: frozenset(),
}


def assert_mode_transition(current: ShadowMode, target: ShadowMode) -> None:
    if target is current:
        return
    if target not in _MODE[current]:
        raise InvalidShadowTransition(
            f"illegal shadow mode transition: {current.value} → {target.value}"
        )


def assert_cycle_transition(current: CycleStatus, target: CycleStatus) -> None:
    if target is current:
        raise InvalidShadowTransition(f"no-op cycle transition is not recorded: {current.value}")
    if target not in _CYCLE[current]:
        raise InvalidShadowTransition(
            f"illegal shadow cycle transition: {current.value} → {target.value}"
        )


def assert_order_transition(current: ShadowOrderStatus, target: ShadowOrderStatus) -> None:
    if target is current:
        raise InvalidShadowTransition(f"no-op shadow order transition: {current.value}")
    if target not in _ORDER[current]:
        raise InvalidShadowTransition(
            f"illegal shadow order transition: {current.value} → {target.value}"
        )


def advance_order(
    current: ShadowOrderStatus, target: ShadowOrderStatus
) -> ShadowOrderStatus:
    assert_order_transition(current, target)
    return target
