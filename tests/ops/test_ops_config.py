from __future__ import annotations

from quantlab.ops.config import OpsConfig, detect_mutation


def test_configuration_hash_changes_are_detected() -> None:
    first = OpsConfig(config_id="a")
    second = OpsConfig(config_id="b")
    assert first.config_hash() != second.config_hash()
    assert detect_mutation(second, first.config_hash())
