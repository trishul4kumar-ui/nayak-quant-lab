"""Environment identity. Production config must not be used as research."""

from __future__ import annotations

from quantlab.core.config import get_settings
from quantlab.ops.errors import OpsError
from quantlab.ops.models import EnvironmentName


def current_environment() -> EnvironmentName:
    raw = get_settings().quant_lab_env.lower()
    mapping = {item.value: item for item in EnvironmentName}
    return mapping.get(raw, EnvironmentName.RESEARCH)


def reject_confusion(*, declared: EnvironmentName, credentials: str) -> None:
    if declared is EnvironmentName.PRODUCTION and credentials == "research":
        raise OpsError("research credentials must not be interpreted as production")
    if declared is EnvironmentName.RESEARCH and credentials == "production":
        raise OpsError("production configuration must not be used in research")
