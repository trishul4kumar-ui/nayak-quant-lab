"""Production data admission. Synthetic examples belong to isolated tests only.

The private fixture switch is set by tests/conftest.py and inherited by spawned
test workers. The desktop launcher clears it. Never infer REAL from connectivity,
an absent label, or a renamed synthetic artifact.
"""

from __future__ import annotations

import os

from quantlab.core.errors import DataIntegrityError


def fixtures_enabled() -> bool:
    return os.environ.get("_QUANTLAB_TEST_FIXTURES") == "1"


def require_test_fixtures(source: str) -> None:
    if not fixtures_enabled():
        raise DataIntegrityError(
            f"REAL_DATA_REQUIRED: {source} is a test fixture, not a production source. "
            "Connect Kite for quotes/history/account observations or supply a verified "
            "REAL dataset. No synthetic fallback was executed."
        )


def require_real_data(data_kind: str, *, source: str) -> None:
    if not fixtures_enabled() and (
        data_kind.strip().lower() != "real"
        or not source.strip()
        or source.lower().startswith(("mock", "synthetic", "memory_synthetic"))
    ):
        raise DataIntegrityError(
            f"REAL_DATA_REQUIRED: {source} has data_kind={data_kind or 'unknown'}. "
            "Existing evidence is preserved but cannot drive a new production calculation."
        )
