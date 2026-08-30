from __future__ import annotations

import pytest

from quantlab.ops.environment import EnvironmentName, reject_confusion
from quantlab.ops.errors import OpsError


def test_environment_confusion_is_rejected() -> None:
    with pytest.raises(OpsError):
        reject_confusion(declared=EnvironmentName.PRODUCTION, credentials="research")
    with pytest.raises(OpsError):
        reject_confusion(declared=EnvironmentName.RESEARCH, credentials="production")
