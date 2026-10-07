"""Small explicit lifecycle graph. It contains no live-eligibility state."""

from quantlab.trade_candidates.models import CandidateStatus

_ALLOWED: dict[CandidateStatus, frozenset[CandidateStatus]] = {
    CandidateStatus.DRAFT: frozenset(
        {CandidateStatus.GATHERING_EVIDENCE, CandidateStatus.REJECTED}
    ),
    CandidateStatus.GATHERING_EVIDENCE: frozenset(
        {CandidateStatus.VALIDATING, CandidateStatus.BLOCKED}
    ),
    CandidateStatus.VALIDATING: frozenset(
        {CandidateStatus.READY_FOR_REVIEW, CandidateStatus.BLOCKED}
    ),
    CandidateStatus.READY_FOR_REVIEW: frozenset(
        {
            CandidateStatus.WATCH,
            CandidateStatus.PAPER_ELIGIBLE,
            CandidateStatus.REJECTED,
            CandidateStatus.EXPIRED,
        }
    ),
    CandidateStatus.WATCH: frozenset(
        {CandidateStatus.READY_FOR_REVIEW, CandidateStatus.REJECTED, CandidateStatus.EXPIRED}
    ),
    CandidateStatus.PAPER_ELIGIBLE: frozenset(
        {CandidateStatus.SHADOW_ELIGIBLE, CandidateStatus.EXPIRED, CandidateStatus.BLOCKED}
    ),
    CandidateStatus.SHADOW_ELIGIBLE: frozenset(
        {CandidateStatus.EXPIRED, CandidateStatus.BLOCKED}
    ),
    CandidateStatus.BLOCKED: frozenset(
        {CandidateStatus.VALIDATING, CandidateStatus.EXPIRED}
    ),
    CandidateStatus.EXPIRED: frozenset(),
    CandidateStatus.REJECTED: frozenset(),
}


def ensure_transition(current: CandidateStatus, target: CandidateStatus) -> None:
    if target not in _ALLOWED[current]:
        raise ValueError(f"candidate transition {current}->{target} is forbidden")
