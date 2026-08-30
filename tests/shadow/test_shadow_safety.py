from pathlib import Path

import pytest

from quantlab.core.config import LiveSafetyGates
from quantlab.core.errors import (
    CheckpointError,
    InvalidShadowTransition,
    LiveRouteAttempt,
    SafetyError,
    ShadowCertificationError,
    ShadowError,
)
from quantlab.domain.research import CheckResult
from quantlab.paper_oms.state import reset as reset_paper
from quantlab.shadow.cycle import (
    assert_cycle_transition,
    assert_mode_transition,
    assert_order_transition,
)
from quantlab.shadow.enums import CycleStatus, KillReason, ShadowMode, ShadowOrderStatus
from quantlab.shadow.models import ShadowRequest
from quantlab.shadow.recovery import recover
from quantlab.shadow.service import halt, run_shadow_cycle, start
from quantlab.shadow.state import reset as reset_shadow

pytestmark = pytest.mark.shadow


@pytest.fixture(autouse=True)
def _isolate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "quantlab.shadow.checkpoint.default_path",
        lambda: tmp_path / "shadow_checkpoint.json",
    )
    reset_shadow()
    reset_paper()
    yield
    reset_shadow()
    reset_paper()


def test_live_trading_impossible() -> None:
    with pytest.raises(SafetyError):
        run_shadow_cycle(ShadowRequest(live_trading=True))


def test_live_route_attempt() -> None:
    with pytest.raises(LiveRouteAttempt):
        run_shadow_cycle(ShadowRequest(route_live=True))


def test_ai_cannot_override() -> None:
    with pytest.raises(ShadowError, match="AI_SUGGESTION"):
        run_shadow_cycle(ShadowRequest(ai_override=True))


@pytest.mark.parametrize("name", ["BROKER_PASSWORD", "LIVE_ACCOUNT_ID", "LIVE_ORDER_TOKEN"])
def test_broker_env_rejected(name: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(name, "secret")
    with pytest.raises(ShadowError, match="credentials"):
        run_shadow_cycle()


def test_broker_imports_absent() -> None:
    root = Path("src/quantlab/shadow")
    text = "\n".join(path.read_text(encoding="utf-8") for path in root.rglob("*.py"))
    for forbidden in (
        "kiteconnect",
        "zerodha",
        "openalgo",
        "quantlab.brokers",
        "BrokerAdapter",
        "LiveOrderRouter",
        "LiveOrderSubmitter",
    ):
        assert forbidden not in text


def test_kill_switch_rejects_new_exposure() -> None:
    run_shadow_cycle()
    halt(reason=KillReason.MANUAL_HALT)
    with pytest.raises(ShadowError, match="HALT"):
        run_shadow_cycle()


def test_halt_is_not_autoliquidate() -> None:
    first = run_shadow_cycle()
    held = dict(first.portfolio.positions)
    halt(reason=KillReason.MANUAL_HALT)
    with pytest.raises(ShadowError):
        run_shadow_cycle()
    from quantlab.shadow.state import last_result

    still = last_result()
    assert still is not None
    assert still.portfolio.positions == held


def test_paper_mode_without_cert_is_not_production() -> None:
    result = run_shadow_cycle(ShadowRequest(mode=ShadowMode.PAPER))
    assert result.cycle.production_run is False
    assert result.cycle.requested_mode is ShadowMode.PAPER
    assert result.cycle.mode is ShadowMode.RESEARCH_PAPER
    assert result.integrity.checks["certification_expired"] is CheckResult.FAIL


def test_require_certified_halts() -> None:
    with pytest.raises(ShadowCertificationError):
        run_shadow_cycle(ShadowRequest(mode=ShadowMode.SHADOW, require_certified=True))


def test_recovery_without_reconciliation_fails() -> None:
    with pytest.raises(ShadowError, match="recovery_without_reconciliation"):
        run_shadow_cycle(ShadowRequest(skip_reconciliation=True))


def test_checkpoint_restore(tmp_path: Path) -> None:
    result = run_shadow_cycle()
    restored = recover(tmp_path / "shadow_checkpoint.json")
    assert restored.cycle.cycle_id == result.cycle.cycle_id
    assert restored.checkpoint is not None
    assert restored.checkpoint.payload_hash == result.checkpoint.payload_hash


def test_corrupt_checkpoint(tmp_path: Path) -> None:
    path = tmp_path / "shadow_checkpoint.json"
    path.write_text("{not-json", encoding="utf-8")
    with pytest.raises(CheckpointError, match="corrupt"):
        recover(path)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (ShadowMode.HALTED, ShadowMode.PAPER),
        (ShadowMode.OFF, ShadowMode.PAUSED),
        (ShadowMode.RESEARCH_PAPER, ShadowMode.PAPER),
    ],
)
def test_illegal_mode_transitions(current: ShadowMode, target: ShadowMode) -> None:
    with pytest.raises(InvalidShadowTransition):
        assert_mode_transition(current, target)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (CycleStatus.COMPLETED, CycleStatus.CREATED),
        (CycleStatus.CREATED, CycleStatus.COMPLETED),
    ],
)
def test_illegal_cycle_transitions(current: CycleStatus, target: CycleStatus) -> None:
    with pytest.raises(InvalidShadowTransition):
        assert_cycle_transition(current, target)


def test_illegal_order_transition() -> None:
    with pytest.raises(InvalidShadowTransition):
        assert_order_transition(ShadowOrderStatus.RECONCILED, ShadowOrderStatus.CREATED)


def test_safety_gates() -> None:
    gates = LiveSafetyGates()
    assert gates.live_trading is False
    assert gates.shadow_mode is True
    assert gates.broker_routing_enabled is False
    assert gates.live_order_submission_enabled is False


def test_start_from_off() -> None:
    assert start(ShadowMode.RESEARCH_PAPER) is ShadowMode.RESEARCH_PAPER
