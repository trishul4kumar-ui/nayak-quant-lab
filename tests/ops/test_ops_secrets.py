from __future__ import annotations

import pytest

from quantlab.ops.errors import OpsError, SecretExposureError
from quantlab.ops.logging import info
from quantlab.ops.secrets import audit_access, mark_expired, reference, reset_for_tests


def test_secret_values_never_appear_in_logs() -> None:
    text = info("token=super-secret", secrets=("super-secret",))
    assert "super-secret" not in text
    assert "[REDACTED]" in text


def test_expired_secrets_produce_failure() -> None:
    reset_for_tests()
    mark_expired("research-token")
    with pytest.raises(OpsError):
        reference("research-token")


def test_secret_access_to_logs_fails() -> None:
    with pytest.raises(SecretExposureError):
        audit_access(name="x", actor="test", purpose="log")
