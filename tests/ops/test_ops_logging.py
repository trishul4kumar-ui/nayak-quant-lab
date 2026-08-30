from __future__ import annotations

from quantlab.ops.logging import info


def test_logging_redacts_secrets() -> None:
    text = info("token=abc", secrets=("abc",))
    assert "abc" not in text
    assert "[REDACTED]" in text
