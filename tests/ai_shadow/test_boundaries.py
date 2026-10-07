from pathlib import Path


def test_shadow_boundary_exposes_zero_broker_writes_only() -> None:
    source = Path("src/quantlab/ai_shadow.py").read_text()
    assert "broker_writes=0" in source
    assert "NO BROKER WRITE" in source
