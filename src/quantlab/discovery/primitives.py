"""Primitives. Forward labels are not in this library."""

from __future__ import annotations

from quantlab.discovery.definitions import FORBIDDEN_PRIMITIVES
from quantlab.discovery.errors import DiscoveryError
from quantlab.features.registry import list_features

ALLOWED_FEATURES = (
    "momentum_5",
    "momentum_10",
    "momentum_20",
    "rolling_mean_20",
    "rolling_std_20",
)


def allowed_feature_ids() -> tuple[str, ...]:
    registered = {item.feature_id for item in list_features()}
    return tuple(name for name in ALLOWED_FEATURES if name in registered)


def assert_not_label(name: str) -> None:
    lowered = name.lower()
    if (
        lowered in FORBIDDEN_PRIMITIVES
        or lowered.startswith("forward_")
        or lowered.startswith("future_")
    ):
        raise DiscoveryError(f"label primitive forbidden in generation: {name}")
