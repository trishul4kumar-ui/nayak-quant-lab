from __future__ import annotations

import pytest

from quantlab.realtime_data.errors import RealTimeDataError
from quantlab.realtime_data.mock import seed_observations
from quantlab.realtime_data.production import ProductionFeedSource, ProductionMarketDataAdapter
from quantlab.realtime_data.service import reset_for_tests, snapshot, start

pytestmark = pytest.mark.realtime_data


@pytest.fixture(autouse=True)
def _reset() -> None:
    reset_for_tests()


def test_production_adapter_rejects_guessed_identity_and_never_uses_mock_fallback() -> None:
    adapter = ProductionMarketDataAdapter((ProductionFeedSource("fixture-primary", 1),))
    rows = tuple(
        row.model_copy(update={"source": "fixture-primary"}) for row in seed_observations()
    )
    assert adapter.ingest("fixture-primary", rows) == 2
    start(adapter=adapter)
    frozen = snapshot()
    assert frozen.extras["active_source"] == "fixture-primary"
    assert frozen.extras["source_manifest"] == "production-observe-only:fixture-primary"

    reset_for_tests()
    adapter = ProductionMarketDataAdapter((ProductionFeedSource("fixture-primary", 1),))
    start(adapter=adapter)
    with pytest.raises(RealTimeDataError, match="refusing synthetic fallback"):
        snapshot()


def test_production_failover_is_explicit_and_recorded() -> None:
    adapter = ProductionMarketDataAdapter(
        (ProductionFeedSource("primary", 1), ProductionFeedSource("secondary", 2))
    )
    adapter.connect()
    adapter.mark_source_unavailable("primary", reason="fixture_failure")
    health = adapter.source_health()
    assert health["active_source"] == "secondary"
    assert health["source_switches"]
