"""Canonical hashes for econometric objects."""

from __future__ import annotations

from typing import Any

from quantlab.backtest.spec import config_hash
from quantlab.econometrics.models import EconometricRun, EconometricSpecification


def _dump(payload: dict[str, Any]) -> str:
    return config_hash(payload)


def hash_spec(spec: EconometricSpecification) -> str:
    return _dump(spec.model_dump(mode="json", exclude={"note"}))


def hash_run(run: EconometricRun) -> str:
    return _dump(run.model_dump(mode="json", exclude={"run_hash", "note"}))


def idempotency_key(*, spec_id: str, as_of: str, seed: int, n: int, version: str) -> str:
    return _dump(
        {
            "spec_id": spec_id,
            "as_of": as_of,
            "seed": seed,
            "n": n,
            "version": version,
        }
    )
