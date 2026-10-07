"""Simple offline reliability scoring with strict realized-time boundaries."""

from collections import Counter
from datetime import UTC, datetime

from quantlab.agent_calibration.models import (
    AgentScorecard,
    CalibrationPolicy,
    RealizedOutcome,
    ReliabilityBin,
    ScoreStatus,
)

POLICY_TIME = datetime(2026, 10, 7, tzinfo=UTC)
type Warnings = tuple[str, ...]


def default_calibration_policy() -> CalibrationPolicy:
    return CalibrationPolicy(
        created_at=POLICY_TIME,
        schema_version="agent-calibration-v1",
        policy_id="48-v1",
        minimum_sample_size=20,
        bin_count=5,
    )


def _hit(outcome: RealizedOutcome) -> float | None:
    if outcome.realized_return is None:
        return None
    if outcome.stance.value == "LONG":
        return float(outcome.realized_return > 0)
    if outcome.stance.value == "BEARISH":
        return float(outcome.realized_return < 0)
    return None


def score_agent(
    outcomes: tuple[RealizedOutcome, ...],
    *,
    as_of: datetime,
    policy: CalibrationPolicy | None = None,
) -> AgentScorecard:
    """Score only known realized outcomes; never use a future label at prediction time."""
    if as_of.tzinfo is None:
        raise ValueError("scorecard as_of must be timezone-aware")
    policy = (policy or default_calibration_policy()).verified()
    frozen = tuple(item.verified() for item in outcomes)
    if not frozen:
        raise ValueError("at least one realized outcome is required")
    if any(item.realized_at > as_of for item in frozen):
        raise ValueError("future realized outcome is forbidden")
    identities = {(item.agent_id, item.agent_version) for item in frozen}
    if len(identities) != 1:
        raise ValueError("a scorecard covers exactly one agent version")
    agent_id, agent_version = next(iter(identities))
    observed = tuple((item, _hit(item)) for item in frozen)
    scored = tuple((item, hit) for item, hit in observed if hit is not None)
    sample_size = len(scored)
    coverage = sample_size / len(frozen)
    bins = []
    for index in range(policy.bin_count):
        lower, upper = index / policy.bin_count, (index + 1) / policy.bin_count
        rows = tuple(
            (item, hit)
            for item, hit in scored
            if lower <= item.raw_confidence < upper
            or (index == policy.bin_count - 1 and item.raw_confidence == 1)
        )
        bins.append(
            ReliabilityBin(
                created_at=as_of,
                schema_version="agent-calibration-v1",
                lower=lower,
                upper=upper,
                sample_size=len(rows),
                mean_raw_confidence=(
                    sum(item.raw_confidence for item, _ in rows) / len(rows) if rows else None
                ),
                realized_hit_rate=(sum(hit for _, hit in rows) / len(rows) if rows else None),
            )
        )
    counts = Counter(item.regime for item, _ in scored)
    warning: Warnings = ()
    status = ScoreStatus.RELEASED
    brier = None
    hit_rate = None
    calibrated = None
    if sample_size < policy.minimum_sample_size:
        status = ScoreStatus.NOT_TESTED
        warning = ("INSUFFICIENT_OOS_SAMPLE", "RAW_CONFIDENCE_IS_NOT_CALIBRATED")
    else:
        hit_rate = sum(hit for _, hit in scored) / sample_size
        brier = sum((item.raw_confidence - hit) ** 2 for item, hit in scored) / sample_size
        calibrated = hit_rate
    return AgentScorecard(
        created_at=as_of,
        schema_version="agent-calibration-v1",
        agent_id=agent_id,
        agent_version=agent_version,
        window_start=min(item.prediction_time for item in frozen),
        window_end=as_of,
        status=status,
        sample_size=sample_size,
        coverage=coverage,
        brier_score=brier,
        hit_rate=hit_rate,
        calibrated_confidence=calibrated,
        reliability=tuple(bins),
        regime_sample_sizes=tuple(sorted(counts.items())),
        warnings=warning,
    )
