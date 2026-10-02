from quantlab.ai.permissions import AiCapability, AiPermissions
from quantlab.core.config import LiveSafetyGates


def test_live_gates_default_closed() -> None:
    gates = LiveSafetyGates()
    assert gates.all_pass() is False
    assert "live_trading" in gates.blocking_reasons()


def test_live_gates_require_routing_controls_and_shadow_exit() -> None:
    gates = LiveSafetyGates(
        live_trading=True,
        live_trading_enabled=True,
        broker_connected=True,
        strategy_approved=True,
        model_approved=True,
        session_valid=True,
    )

    assert gates.all_pass() is False
    assert "broker_routing_enabled" in gates.blocking_reasons()
    assert "broker_write_enabled" in gates.blocking_reasons()
    assert "shadow_mode" in gates.blocking_reasons()


def test_ai_cannot_request_live_order() -> None:
    perms = AiPermissions()
    assert perms.allows(AiCapability.READ_MARKET_DATA)
    assert perms.allows(AiCapability.REQUEST_LIVE_ORDER) is False
    assert perms.allows(AiCapability.OVERRIDE_RESEARCH_GATE) is False
