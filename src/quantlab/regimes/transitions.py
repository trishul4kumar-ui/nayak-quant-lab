"""Empirical regime transitions. Rows must be probabilities."""

from __future__ import annotations

from pydantic import BaseModel, Field

from quantlab.core.errors import RegimeError
from quantlab.domain.research import CheckResult
from quantlab.regimes.detectors import RegimeObservation


class TransitionMatrix(BaseModel):
    schema_version: str = "1"
    labels: list[str] = Field(default_factory=list)
    counts: list[list[int]] = Field(default_factory=list)
    probabilities: list[list[float]] = Field(default_factory=list)
    n_transitions: int = 0
    status: CheckResult = CheckResult.PASS
    note: str = "P(R_{t+1}=j | R_t=i) from consecutive hard labels; not a forecast"


def transition_matrix(observations: list[RegimeObservation]) -> TransitionMatrix:
    seq = [row.hard_label for row in observations if row.hard_label is not None]
    labels = sorted(set(seq))
    if len(seq) < 2 or len(labels) < 1:
        return TransitionMatrix(
            status=CheckResult.NOT_TESTED,
            note="insufficient consecutive labels",
        )
    index = {name: i for i, name in enumerate(labels)}
    n = len(labels)
    counts = [[0 for _ in range(n)] for _ in range(n)]
    prev: str | None = None
    total = 0
    for obs in observations:
        label = obs.hard_label
        if label is None:
            prev = None
            continue
        if prev is not None:
            counts[index[prev]][index[label]] += 1
            total += 1
        prev = label
    probs: list[list[float]] = []
    for i, row in enumerate(counts):
        s = sum(row)
        if s == 0:
            ident = [0.0] * n
            ident[i] = 1.0
            probs.append(ident)
            continue
        probs.append([c / s for c in row])
        if abs(sum(probs[-1]) - 1.0) > 1e-8:
            raise RegimeError(f"transition row {labels[i]} does not sum to 1")
        if any(p < -1e-12 for p in probs[-1]):
            raise RegimeError("negative transition probability")
    return TransitionMatrix(
        labels=labels,
        counts=counts,
        probabilities=probs,
        n_transitions=total,
    )
