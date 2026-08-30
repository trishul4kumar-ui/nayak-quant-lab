from __future__ import annotations

from datetime import UTC, datetime

import pytest

from quantlab import __version__
from quantlab.ops.errors import OpsError
from quantlab.ops.models import EnvironmentName, ReleaseIdentity
from quantlab.ops.release import assert_identity, current_release


def test_release_identity_mismatch_is_detected() -> None:
    good = current_release()
    assert good.software_version == __version__
    bad = ReleaseIdentity(
        software_version="0.0.0",
        config_hash=good.config_hash,
        environment=EnvironmentName.RESEARCH,
        timestamp=datetime(2024, 1, 2, tzinfo=UTC),
    )
    with pytest.raises(OpsError):
        assert_identity(bad)
