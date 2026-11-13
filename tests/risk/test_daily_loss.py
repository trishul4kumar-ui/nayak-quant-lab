from __future__ import annotations

from dataclasses import replace
from datetime import UTC, date, datetime, timedelta

import pytest

from quantlab.core.errors import RiskRejectedError
from quantlab.core.identifiers import InstrumentId
from quantlab.domain.models import Instrument, ProposedPortfolio, RiskVerdict, TargetPosition
from quantlab.risk.firewall import DailyLossEvidence, DailyLossPolicy, RiskFirewall

AS_OF = datetime(2024, 1, 2, 10, tzinfo=UTC)


def firewall() -> RiskFirewall:
    result = RiskFirewall(
        daily_loss_policy=DailyLossPolicy(
            max_loss_fraction=0.05, max_age_seconds=60, market_timezone="Asia/Kolkata"
        )
    )
    result.register_instruments([Instrument(id=InstrumentId.parse("NSE:TCS"))])
    return result


def proposal() -> ProposedPortfolio:
    return ProposedPortfolio(
        as_of=AS_OF,
        targets=[TargetPosition(instrument=InstrumentId.parse("NSE:TCS"), weight=0.2)],
    )


def evidence() -> DailyLossEvidence:
    return DailyLossEvidence(
        session_date=date(2024, 1, 2), opening_equity=100.0, current_equity=98.0,
        observed_at=AS_OF - timedelta(seconds=10), available_at=AS_OF - timedelta(seconds=5),
        source="test-fixture", source_checksum="a" * 64, cash_flow_adjusted=True,
    )


def test_missing_evidence_rejects_only_when_guard_is_configured() -> None:
    guard = firewall()
    assert guard.authorize(proposal()).reasons == ["daily_loss_evidence_missing"]
    with pytest.raises(RiskRejectedError):
        guard.require(proposal())
    assert guard.authorize(proposal(), daily_loss=evidence()).verdict is RiskVerdict.APPROVE


def test_loss_at_or_above_limit_rejects_but_gain_is_not_a_loss() -> None:
    guard = firewall()
    for equity in (95.0, 90.0):
        result = guard.authorize(proposal(), daily_loss=replace(evidence(), current_equity=equity))
        assert result.verdict is RiskVerdict.REJECT
        assert result.reasons == ["daily_loss_limit"]
        assert result.modified is None
    assert guard.authorize(
        proposal(), daily_loss=replace(evidence(), current_equity=101.0)
    ).verdict is RiskVerdict.APPROVE


@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        ({"available_at": AS_OF + timedelta(seconds=1)}, "daily_loss_evidence_time_invalid"),
        ({"observed_at": AS_OF + timedelta(seconds=1)}, "daily_loss_evidence_time_invalid"),
        ({"observed_at": AS_OF - timedelta(seconds=61)}, "daily_loss_evidence_stale"),
        ({"session_date": date(2024, 1, 1)}, "daily_loss_session_mismatch"),
        ({"opening_equity": 0.0}, "daily_loss_evidence_invalid"),
        ({"current_equity": float("nan")}, "daily_loss_evidence_invalid"),
        ({"current_equity": float("inf")}, "daily_loss_evidence_invalid"),
        ({"opening_equity": 1e-320, "current_equity": 1e300}, "daily_loss_evidence_invalid"),
        ({"source": ""}, "daily_loss_evidence_invalid"),
        ({"source_checksum": "invalid"}, "daily_loss_evidence_invalid"),
        ({"cash_flow_adjusted": False}, "daily_loss_evidence_invalid"),
        ({"source": None}, "daily_loss_evidence_invalid"),
        ({"source_checksum": None}, "daily_loss_evidence_invalid"),
        ({"opening_equity": "100"}, "daily_loss_evidence_invalid"),
        ({"current_equity": None}, "daily_loss_evidence_invalid"),
        ({"current_equity": 10**500}, "daily_loss_evidence_invalid"),
        ({"observed_at": None}, "daily_loss_evidence_time_invalid"),
        ({"available_at": "2024-01-02"}, "daily_loss_evidence_time_invalid"),
    ],
)
def test_inadequate_evidence_fails_closed(changes: dict[str, object], reason: str) -> None:
    item = replace(evidence(), **changes)  # type: ignore[arg-type]
    decision = firewall().authorize(proposal(), daily_loss=item)
    assert decision.verdict is RiskVerdict.REJECT
    assert decision.reasons == [reason]


@pytest.mark.parametrize(
    ("loss", "age", "timezone"),
    [
        (0.0, 1.0, "Asia/Kolkata"),
        (float("nan"), 1.0, "Asia/Kolkata"),
        (0.1, float("inf"), "Asia/Kolkata"),
        (0.1, -1.0, "Asia/Kolkata"),
        (0.1, 1.0, "not-a-timezone"),
    ],
)
def test_invalid_policies_rejected(loss: float, age: float, timezone: str) -> None:
    with pytest.raises(ValueError):
        DailyLossPolicy(max_loss_fraction=loss, max_age_seconds=age, market_timezone=timezone)
