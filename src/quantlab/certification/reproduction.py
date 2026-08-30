"""Reproduction hashes. Difference is a break, not a warning."""

from __future__ import annotations

from quantlab.certification.identity import hash_validation
from quantlab.certification.models import Candidate, ChecklistItem, ReproductionResult
from quantlab.core.errors import ReproductionBreak
from quantlab.research.envinfo import environment


def reproduce(
    candidate: Candidate,
    items: list[ChecklistItem],
    *,
    expected_hash: str,
) -> ReproductionResult:
    actual = hash_validation(candidate, items)
    matched = actual == expected_hash and bool(expected_hash)
    result = ReproductionResult(
        matched=matched,
        expected_hash=expected_hash,
        actual_hash=actual,
        environment=str(environment().get("python", "")),
        note=(
            "Reproduction hashes match."
            if matched
            else "REPRODUCTION_BREAK: frozen validation hash does not match replay."
        ),
    )
    if not matched:
        raise ReproductionBreak(result.note)
    return result
