from quantlab.app.mode import AppMode, resolve_mode
from quantlab.core.config import LiveSafetyGates


def test_live_mode_requires_all_gates() -> None:
    gates = LiveSafetyGates()
    assert gates.all_pass() is False
    assert resolve_mode("live", gates) is AppMode.RESEARCH
    assert resolve_mode("research", gates) is AppMode.RESEARCH
    assert resolve_mode("paper", gates) is AppMode.PAPER
    assert resolve_mode("not-a-mode", gates) is AppMode.RESEARCH
