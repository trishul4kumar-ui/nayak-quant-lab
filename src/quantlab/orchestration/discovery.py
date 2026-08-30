"""Discovery is not confirmation. A family search records every trial."""

from __future__ import annotations

from pydantic import BaseModel

from quantlab.orchestration.contracts import ResearchQuality
from quantlab.orchestration.selection import CandidateOutcome


class DiscoverySummary(BaseModel):
    hypothesis_id: str
    family_id: str
    attempted: int
    failed: int
    rejected: int
    survived_discovery: int
    quality: ResearchQuality = ResearchQuality.EXPLORATORY
    note: str = "Discovery is not validation and not promotion."


def summarize_discovery(
    hypothesis_id: str,
    family_id: str,
    outcomes: list[CandidateOutcome],
) -> DiscoverySummary:
    failed = sum(1 for item in outcomes if item.failed)
    survived = sum(1 for item in outcomes if not item.failed)
    return DiscoverySummary(
        hypothesis_id=hypothesis_id,
        family_id=family_id,
        attempted=len(outcomes),
        failed=failed,
        rejected=failed,
        survived_discovery=survived,
        quality=ResearchQuality.EXPLORATORY if survived else ResearchQuality.INCONCLUSIVE,
    )
