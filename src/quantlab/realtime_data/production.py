"""Provider-neutral production feed boundary, backed by injected observations."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import UTC, datetime

from quantlab.realtime_data.errors import RealTimeDataError
from quantlab.realtime_data.models import MarketObservation, QualityStatus


@dataclass(frozen=True)
class ProductionFeedSource:
    source_id: str
    priority: int


class ProductionMarketDataAdapter:
    """Observe-only provider bridge boundary; it contains no vendor SDK or endpoint."""

    write_enabled = False

    def __init__(
        self,
        sources: tuple[ProductionFeedSource, ...],
        *,
        expected_security_ids: frozenset[str] = frozenset(),
    ) -> None:
        if not sources:
            raise ValueError("production adapter requires at least one source")
        ids = [item.source_id for item in sources]
        if len(ids) != len(set(ids)):
            raise ValueError("production source ids must be unique")
        self._sources = tuple(sorted(sources, key=lambda item: item.priority))
        self.source_id = self._sources[0].source_id
        self._expected_security_ids = expected_security_ids
        self._connected = False
        self._queues = {item.source_id: deque[MarketObservation]() for item in self._sources}
        self._unavailable: set[str] = set()
        self._switches: list[str] = []
        self._faults: list[str] = []
        self._last_prices: dict[str, float] = {}
        self._observed_security_ids: set[str] = set()

    @property
    def source_priority(self) -> tuple[str, ...]:
        return tuple(item.source_id for item in self._sources)

    @property
    def source_switches(self) -> tuple[str, ...]:
        return tuple(self._switches)

    @property
    def quality_faults(self) -> tuple[str, ...]:
        return tuple(self._faults)

    def connect(self) -> None:
        self._connected = True
        self._select_source(reason="connect")

    def disconnect(self) -> None:
        self._connected = False

    def ingest(self, source_id: str, observations: tuple[MarketObservation, ...]) -> int:
        """Accept provider output only when identity and source provenance are explicit."""
        if source_id not in self._queues:
            raise RealTimeDataError("observation source is not configured")
        accepted = 0
        for row in observations:
            if row.source != source_id:
                self._faults.append("source_provenance_break")
                continue
            if row.security_id.startswith("UNMAPPED:") or (
                self._expected_security_ids and row.security_id not in self._expected_security_ids
            ):
                self._faults.append("security_mapping_guess")
                continue
            if row.live_trading:
                self._faults.append("live_trading_flag_rejected")
                continue
            checked = self._quality_checked(row)
            self._queues[source_id].append(checked)
            self._observed_security_ids.add(checked.security_id)
            accepted += 1
        return accepted

    def mark_source_unavailable(self, source_id: str, *, reason: str = "unavailable") -> None:
        if source_id not in self._queues:
            raise RealTimeDataError("source is not configured")
        self._unavailable.add(source_id)
        prior = self.source_id
        self._select_source(reason=reason)
        if self.source_id == prior and prior in self._unavailable:
            self._faults.append("production_feed_unavailable")

    def restore_source(self, source_id: str) -> None:
        self._unavailable.discard(source_id)

    def poll(self) -> tuple[MarketObservation, ...]:
        if not self._connected or self.source_id in self._unavailable:
            return ()
        rows = tuple(self._queues[self.source_id])
        self._queues[self.source_id].clear()
        return rows

    def source_health(self) -> dict[str, object]:
        return {
            "active_source": self.source_id,
            "source_priority": self.source_priority,
            "source_switches": self.source_switches,
            "quality_faults": self.quality_faults,
            "connected": self._connected,
            "unavailable": tuple(sorted(self._unavailable)),
            "coverage": (
                len(self._observed_security_ids & self._expected_security_ids)
                / len(self._expected_security_ids)
                if self._expected_security_ids
                else None
            ),
        }

    def _select_source(self, *, reason: str) -> None:
        available = next(
            (item.source_id for item in self._sources if item.source_id not in self._unavailable),
            None,
        )
        if available is None:
            raise RealTimeDataError("no production market-data source available")
        if available != self.source_id:
            switch = f"{self.source_id}->{available}:{reason}:{datetime.now(tz=UTC).isoformat()}"
            self._switches.append(switch)
            self.source_id = available

    def _quality_checked(self, row: MarketObservation) -> MarketObservation:
        degraded = row.quality is QualityStatus.DEGRADED
        if (
            row.bid is not None
            and row.ask is not None
            and row.bid > 0
            and row.ask > 0
            and row.bid >= row.ask
        ):
            self._faults.append("crossed_or_locked_quote")
            degraded = True
        if row.price is not None:
            previous = self._last_prices.get(row.security_id)
            if previous and abs(row.price - previous) / previous > 0.20:
                self._faults.append("abnormal_price_jump")
                degraded = True
            self._last_prices[row.security_id] = row.price
        if degraded and row.quality is QualityStatus.VALID:
            return row.model_copy(update={"quality": QualityStatus.DEGRADED})
        return row
