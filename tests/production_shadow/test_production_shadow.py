from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from quantlab.broker_gateway.mock import MockBrokerAdapter
from quantlab.broker_gateway.models import GatewaySnapshotBundle, Provenance
from quantlab.broker_gateway.repository import put_bundle
from quantlab.broker_gateway.service import matching_internal_books
from quantlab.broker_gateway.service import reset_for_tests as reset_broker
from quantlab.core.config import LiveSafetyGates
from quantlab.execution_authorization.models import (
    AuthorizationEvidence,
    AuthorizationScope,
    AuthorizationState,
)
from quantlab.execution_authorization.repository import reset_for_tests as reset_authorization
from quantlab.execution_authorization.service import assess as assess_authorization
from quantlab.paper_oms.state import reset as reset_paper
from quantlab.production_shadow.models import (
    DigitalTwinReplayEvidence,
    ShadowCheckResult,
    ShadowProductionState,
)
from quantlab.production_shadow.repository import reset_for_tests
from quantlab.production_shadow.service import (
    assess,
    capture_deterministic_replay_evidence,
    start,
    stop,
)
from quantlab.realtime_data.hashing import sha256
from quantlab.realtime_data.kite import (
    KiteHttpResponse,
    KiteMarketDataAdapter,
    KiteMarketDataConfig,
)
from quantlab.realtime_data.mock import seed_observations
from quantlab.realtime_data.models import RealTimeSnapshot
from quantlab.realtime_data.production import ProductionFeedSource, ProductionMarketDataAdapter
from quantlab.realtime_data.service import reset_for_tests as reset_realtime
from quantlab.realtime_data.service import snapshot as freeze_market
from quantlab.realtime_data.service import start as start_market
from quantlab.realtime_decision.models import CertificationStatus, StrategyRelease
from quantlab.realtime_decision.service import reset_for_tests as reset_decision
from quantlab.realtime_decision.service import run_realtime_decision
from quantlab.reconciliation.repository import reset_for_tests as reset_reconciliation
from quantlab.reconciliation.service import internal_from_books, reconcile
from quantlab.release.service import (
    approve as approve_release,
)
from quantlab.release.service import (
    certify as certify_release,
)
from quantlab.release.service import (
    default_passing_request,
)
from quantlab.release.service import (
    reset_for_tests as reset_release,
)
from quantlab.safety.service import reset_for_tests as reset_safety
from quantlab.shadow.service import run_shadow_cycle
from quantlab.shadow.state import reset as reset_shadow

_NOW = datetime(2026, 10, 3, 4, 0, tzinfo=UTC)


class _QuoteTransport:
    def get(
        self, _path: str, _headers: dict[str, str], _timeout_seconds: float
    ) -> KiteHttpResponse:
        payload = {
            "status": "success",
            "data": {
                "NSE:INFY": {
                    "instrument_token": 408065,
                    "last_price": 1500.0,
                    "last_quantity": 10,
                    "volume": 1000,
                    "timestamp": "2026-10-03 09:30:00",
                    "depth": {
                        "buy": [{"price": 1499.95}],
                        "sell": [{"price": 1500.05}],
                    },
                }
            },
        }
        return KiteHttpResponse(status=200, body=json.dumps(payload).encode())


@pytest.fixture(autouse=True)
def _reset(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "quantlab.shadow.checkpoint.default_path",
        lambda: tmp_path / "shadow_checkpoint.json",
    )
    reset_for_tests()
    reset_broker()
    reset_realtime()
    reset_reconciliation()
    reset_decision()
    reset_authorization()
    reset_release()
    reset_safety()
    reset_shadow()
    reset_paper()


def test_missing_production_evidence_fails_closed_without_routing() -> None:
    result = assess()
    assert result.state is ShadowProductionState.BLOCKED
    assert result.non_routable is True
    assert result.live_trading is False
    assert result.broker_write_enabled is False
    assert "market_snapshot" in result.readiness.critical_failures
    assert LiveSafetyGates().all_pass() is False


def test_start_stop_are_assessment_state_only() -> None:
    assert start() is ShadowProductionState.RUNNING
    assert stop() is ShadowProductionState.STOPPED


def test_production_shadow_has_no_broker_write_path() -> None:
    source = "\n".join(
        item.read_text() for item in Path("src/quantlab/production_shadow").glob("*.py")
    )
    for forbidden in ("place_order", "cancel_order", "modify_order"):
        assert forbidden not in source


def _provider_market() -> RealTimeSnapshot:
    fixture_auth = ("fixture-key", "fixture-token")
    adapter = KiteMarketDataAdapter(
        KiteMarketDataConfig(
            api_key=fixture_auth[0],
            access_token=fixture_auth[1],
            symbols="NSE:INFY",
        ),
        transport=_QuoteTransport(),
        clock=lambda: _NOW,
    )
    start_market(adapter=adapter)
    return freeze_market(as_of=_NOW)


def _recorded_broker() -> GatewaySnapshotBundle:
    """A saved read-only broker observation fixture; it is never a write adapter."""
    original = MockBrokerAdapter().snapshot()
    provenance = Provenance(
        adapter_id="recorded-readonly-fixture-v1",
        broker="recorded-provider",
        captured_at=_NOW,
        source_timestamp=_NOW,
        gateway_receipt_at=_NOW,
        source_sequence=1,
    )
    bundle = original.model_copy(
        update={
            "adapter_id": provenance.adapter_id,
            "provenance": provenance,
            "orders": tuple(
                item.model_copy(update={"source_timestamp": _NOW}) for item in original.orders
            ),
            "capture_started_at": _NOW,
            "capture_completed_at": _NOW,
        }
    )
    return put_bundle(bundle)


def _certified_release() -> StrategyRelease:
    return StrategyRelease(
        release_id="recorded-release-v1",
        strategy_id="recorded-strategy",
        version="1",
        feature_manifest_hash="features",
        model_manifest_hash="model",
        portfolio_manifest_hash="portfolio",
        capital_manifest_hash="capital",
        certification_id="cert-recorded",
        certification_status=CertificationStatus.CERTIFIED,
        release_hash="release-hash",
        effective_at=_NOW - timedelta(minutes=1),
    )


def _complete_recorded_chain() -> tuple[object, ...]:
    market = _provider_market()
    broker = _recorded_broker()
    reconciliation = reconcile(
        broker,
        internal_from_books(matching_internal_books(), observed_at=_NOW),
        observed_at=_NOW,
    )
    decision = run_realtime_decision(release=_certified_release(), frozen=market)
    shadow = run_shadow_cycle()
    replay = capture_deterministic_replay_evidence(
        source_run_id="recorded-shadow-chain-v1",
        market=market,
        broker=broker,
        reconciliation=reconciliation,
        decision=decision,
        shadow=shadow,
        observed_at=_NOW,
    )
    return market, broker, reconciliation, decision, shadow, replay


def _rehash_replay(
    replay: DigitalTwinReplayEvidence, **updates: object
) -> DigitalTwinReplayEvidence:
    unsigned = replay.model_copy(update={**updates, "evidence_hash": ""})
    return unsigned.model_copy(
        update={
            "evidence_hash": sha256(unsigned.model_dump(mode="json", exclude={"evidence_hash"}))
        }
    )


def test_complete_recorded_chain_reaches_human_review_eligibility() -> None:
    """Exercise services end-to-end with deterministic recorded provider fixtures.

    The fixtures stand in for previously captured read-only observations.  They
    do not contact a broker and the resulting authorization is still only an
    eligibility assessment, never permission to submit an order.
    """
    market, broker, reconciliation, decision, shadow, replay = _complete_recorded_chain()
    production_shadow = assess(
        market=market,
        broker=broker,
        reconciliation=reconciliation,
        decision=decision,
        shadow=shadow,
        replay=replay,
        observed_at=_NOW,
    )

    assert production_shadow.readiness.critical_failures == ()
    assert production_shadow.state is ShadowProductionState.RUNNING
    assert production_shadow.non_routable is True
    assert (
        next(
            item for item in production_shadow.checks if item.check_id == "deterministic_replay"
        ).result
        is ShadowCheckResult.PASS
    )

    release_request = default_passing_request().model_copy(update={"data_kind": "real"})
    certify_release(release_request)
    approve_release(release_request)
    scope = AuthorizationScope(
        deployment_id="recorded-deployment",
        broker_account_fingerprint=broker.profile.account_id_hash,
        allowed_security_ids=("NSE:INFY",),
        universe_version="recorded-universe-v1",
        strategy_hash="strategy",
        model_hash="model",
        portfolio_policy_hash="portfolio",
        release_id="recorded-release-v1",
        data_provider="kite-rest-quote-v3",
        data_policy_hash=market.snapshot_hash,
        risk_policy_hash="risk-policy",
        max_gross_exposure=1.0,
        max_notional=1000.0,
        max_turnover=0.1,
        operating_mode="restricted_human_review",
        session_start=_NOW - timedelta(minutes=1),
        session_end=_NOW + timedelta(minutes=5),
        expiry=_NOW + timedelta(minutes=10),
    )
    authorization = assess_authorization(
        scope,
        evidence=(
            AuthorizationEvidence(
                source="recorded-audit",
                provenance="hash-verifiable-fixture",
                observed_at=_NOW,
                content_hash=sha256({"market": market.snapshot_hash}),
                report_id=production_shadow.shadow_run_id,
            ),
        ),
        assessed_at=_NOW,
    )
    assert authorization.state is AuthorizationState.ELIGIBLE_FOR_HUMAN_REVIEW
    assert authorization.live_trading is False
    assert authorization.broker_write_enabled is False


def test_replay_evidence_tampering_mismatch_and_staleness_block_readiness() -> None:
    """Every invalid replay mode remains an explicit, critical failed check."""
    market, broker, reconciliation, decision, shadow, replay = _complete_recorded_chain()

    missing = assess(
        market=market,
        broker=broker,
        reconciliation=reconciliation,
        decision=decision,
        shadow=shadow,
        replay=None,
        observed_at=_NOW,
    )
    assert "deterministic_replay" in missing.readiness.critical_failures

    tampered_hash = replay.model_copy(update={"evidence_hash": "0" * 64})
    mismatch = _rehash_replay(replay, decision_hash="different-decision")
    different_account = _rehash_replay(replay, broker_account_fingerprint="other-account")
    stale = replay

    for invalid, now in (
        (tampered_hash, _NOW),
        (mismatch, _NOW),
        (different_account, _NOW),
        (stale, _NOW + timedelta(minutes=6)),
    ):
        run = assess(
            market=market,
            broker=broker,
            reconciliation=reconciliation,
            decision=decision,
            shadow=shadow,
            replay=invalid,
            observed_at=now,
        )
        check = next(item for item in run.checks if item.check_id == "deterministic_replay")
        assert check.result is ShadowCheckResult.FAIL
        assert "deterministic_replay" in run.readiness.critical_failures


def test_synthetic_observations_cannot_be_relabelled_as_production_evidence() -> None:
    adapter = ProductionMarketDataAdapter((ProductionFeedSource("recorded", 1),))
    observations = tuple(
        row.model_copy(update={"source": "recorded"}) for row in seed_observations()
    )
    assert adapter.ingest("recorded", observations) == len(observations)
    start_market(adapter=adapter)
    market = freeze_market(as_of=_NOW)

    run = assess(market=market, observed_at=_NOW)
    market_provenance = next(item for item in run.checks if item.check_id == "market_provenance")
    assert market_provenance.result is ShadowCheckResult.FAIL
