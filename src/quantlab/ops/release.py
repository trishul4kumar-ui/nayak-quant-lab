"""Release identity. Mismatch is FAIL. Not live authorization."""

from __future__ import annotations

from datetime import UTC, datetime

from quantlab import __version__
from quantlab.ops.config import bind
from quantlab.ops.errors import OpsError
from quantlab.ops.models import EnvironmentName, ReleaseIdentity


def current_release() -> ReleaseIdentity:
    cfg = bind()
    return ReleaseIdentity(
        software_version=__version__,
        config_hash=cfg.config_hash(),
        environment=cfg.environment,
        timestamp=datetime(2024, 1, 2, tzinfo=UTC),
    )


def assert_identity(observed: ReleaseIdentity) -> None:
    expected = current_release()
    if observed.software_version != expected.software_version:
        raise OpsError("release identity mismatch")
    if observed.config_hash != expected.config_hash:
        raise OpsError("release identity mismatch")
    if (
        observed.environment is EnvironmentName.PRODUCTION
        and expected.environment is EnvironmentName.RESEARCH
    ):
        raise OpsError("environment confusion")
