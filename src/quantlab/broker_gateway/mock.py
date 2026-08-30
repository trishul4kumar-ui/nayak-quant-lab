"""Deterministic mock adapter for infrastructure tests. Not market evidence."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from quantlab.broker_gateway.errors import BrokerGatewayError, BrokerWriteError
from quantlab.broker_gateway.models import (
    BrokerAccountSnapshot,
    BrokerFillSnapshot,
    BrokerHealth,
    BrokerHoldingSnapshot,
    BrokerMarginSnapshot,
    BrokerOrderSnapshot,
    BrokerPositionSnapshot,
    GatewaySnapshotBundle,
    InstrumentMapping,
    MockScenario,
    Provenance,
)
from quantlab.broker_gateway.secrets import account_id_hash, redact
from quantlab.data.fabric.checksums import sha256_bytes

_AS_OF = datetime(2024, 1, 2, 9, 15, tzinfo=UTC)
_SCHEMA = "2.8.0"


def _hash(*parts: object) -> str:
    return sha256_bytes("|".join(str(item) for item in parts).encode())


class MockBrokerAdapter:
    adapter_id = "mock-readonly-1"
    broker = "mock"

    def __init__(self, scenario: MockScenario = MockScenario.NORMAL) -> None:
        self.scenario = scenario
        self._connected = False
        self._seq = 1

    def connect(self) -> BrokerHealth:
        if self.scenario is MockScenario.CONNECTION_FAILURE:
            raise BrokerGatewayError("mock connection failure")
        if self.scenario is MockScenario.CREDENTIAL_FAILURE:
            raise BrokerGatewayError("credential failure; " + redact())
        self._connected = True
        return self.health()

    def disconnect(self) -> BrokerHealth:
        self._connected = False
        return self.health()

    def health(self) -> BrokerHealth:
        stale = self.scenario is MockScenario.STALE_SNAPSHOT
        if stale:
            state = "stale"
        elif self._connected:
            state = "connected_read_only"
        else:
            state = "disconnected"
        return BrokerHealth(
            state=state,
            healthy=self._connected and not stale,
            stale=stale,
            credential_redacted=redact(),
        )

    def session_status(self) -> Provenance:
        if self.scenario is MockScenario.STALE_SNAPSHOT:
            captured = _AS_OF - timedelta(hours=6)
        else:
            captured = _AS_OF
        seq = 0 if self.scenario is MockScenario.OUT_OF_ORDER else self._seq
        return Provenance(
            adapter_id=self.adapter_id,
            broker=self.broker,
            captured_at=_AS_OF,
            source_timestamp=captured,
            gateway_receipt_at=_AS_OF,
            source_sequence=seq,
        )

    def account(self) -> BrokerAccountSnapshot:
        cash = 80_000.0 if self.scenario is MockScenario.CASH_MISMATCH else 100_000.0
        if self.scenario is MockScenario.PARTIAL_DATA:
            cash = 100_000.0
        prov = self.session_status()
        digest = _hash("acct", cash, prov.source_sequence)
        return BrokerAccountSnapshot(
            snapshot_id=f"acct-{digest[:12]}",
            broker=self.broker,
            account_id_hash=account_id_hash("mock-account"),
            captured_at=prov.captured_at,
            source_timestamp=prov.source_timestamp,
            source_sequence=prov.source_sequence,
            schema_version=_SCHEMA,
            payload_hash=digest,
            available_cash=cash,
            collateral=25_000.0,
            utilized_margin=5_000.0,
            available_margin=20_000.0,
            equity=None if self.scenario is MockScenario.PARTIAL_DATA else 125_000.0,
            buying_power=None if self.scenario is MockScenario.PARTIAL_DATA else 120_000.0,
        )

    def positions(self) -> tuple[BrokerPositionSnapshot, ...]:
        qty = 5.0 if self.scenario is MockScenario.POSITION_MISMATCH else 10.0
        prov = self.session_status()
        digest = _hash("pos", qty, prov.source_sequence)
        row = BrokerPositionSnapshot(
            snapshot_id=f"pos-{digest[:12]}",
            broker=self.broker,
            account_id_hash=account_id_hash("mock-account"),
            captured_at=prov.captured_at,
            source_timestamp=prov.source_timestamp,
            source_sequence=prov.source_sequence,
            schema_version=_SCHEMA,
            payload_hash=digest,
            broker_instrument_id="MOCK-TCS",
            security_id="SEC-TCS",
            exchange="NSE",
            quantity=qty,
            average_price=3500.0,
            last_price=3510.0,
            realized_pnl=0.0,
            unrealized_pnl=100.0,
            product="cnc",
        )
        return (row,)

    def holdings(self) -> tuple[BrokerHoldingSnapshot, ...]:
        prov = self.session_status()
        digest = _hash("hld", 10.0, prov.source_sequence)
        return (
            BrokerHoldingSnapshot(
                snapshot_id=f"hld-{digest[:12]}",
                broker=self.broker,
                account_id_hash=account_id_hash("mock-account"),
                captured_at=prov.captured_at,
                source_timestamp=prov.source_timestamp,
                source_sequence=prov.source_sequence,
                schema_version=_SCHEMA,
                payload_hash=digest,
                broker_instrument_id="MOCK-TCS",
                security_id="SEC-TCS",
                exchange="NSE",
                quantity=10.0,
                average_cost=3400.0,
            ),
        )

    def margins(self) -> BrokerMarginSnapshot:
        prov = self.session_status()
        digest = _hash("mgn", 5000.0, prov.source_sequence)
        return BrokerMarginSnapshot(
            snapshot_id=f"mgn-{digest[:12]}",
            broker=self.broker,
            account_id_hash=account_id_hash("mock-account"),
            captured_at=prov.captured_at,
            source_timestamp=prov.source_timestamp,
            source_sequence=prov.source_sequence,
            schema_version=_SCHEMA,
            payload_hash=digest,
            utilized_margin=5_000.0,
            available_margin=20_000.0,
            collateral=25_000.0,
        )

    def orders(self) -> tuple[BrokerOrderSnapshot, ...]:
        prov = self.session_status()
        digest = _hash("ord", "BRK-ORD-1", prov.source_sequence)
        order = BrokerOrderSnapshot(
            snapshot_id=f"ord-{digest[:12]}",
            broker=self.broker,
            account_id_hash=account_id_hash("mock-account"),
            captured_at=prov.captured_at,
            source_timestamp=prov.source_timestamp,
            source_sequence=prov.source_sequence,
            schema_version=_SCHEMA,
            payload_hash=digest,
            broker_order_id="BRK-ORD-1",
            status="complete",
            side="buy",
            quantity=10.0,
            filled_quantity=10.0,
            pending_quantity=0.0,
            order_type="limit",
            price=3500.0,
            broker_instrument_id="MOCK-TCS",
        )
        if self.scenario is MockScenario.UNKNOWN_ORDER:
            extra_digest = _hash("ord", "BRK-ORD-UNK", prov.source_sequence)
            extra = order.model_copy(
                update={
                    "snapshot_id": f"ord-{extra_digest[:12]}",
                    "payload_hash": extra_digest,
                    "broker_order_id": "BRK-ORD-UNK",
                    "status": "open",
                    "filled_quantity": 0.0,
                    "pending_quantity": 1.0,
                    "quantity": 1.0,
                }
            )
            return (order, extra)
        return (order,)

    def fills(self) -> tuple[BrokerFillSnapshot, ...]:
        prov = self.session_status()
        digest = _hash("fill", "BRK-FILL-1", prov.source_sequence)
        fill = BrokerFillSnapshot(
            snapshot_id=f"fill-{digest[:12]}",
            broker=self.broker,
            account_id_hash=account_id_hash("mock-account"),
            captured_at=prov.captured_at,
            source_timestamp=prov.source_timestamp,
            source_sequence=prov.source_sequence,
            schema_version=_SCHEMA,
            payload_hash=digest,
            broker_fill_id="BRK-FILL-1",
            broker_order_id="BRK-ORD-1",
            quantity=10.0,
            price=3500.0,
            exchange="NSE",
            charges=0.0,
        )
        if self.scenario is MockScenario.DUPLICATE_FILL:
            return (fill, fill)
        if self.scenario is MockScenario.ORPHAN_FILL:
            orphan_digest = _hash("fill", "BRK-FILL-ORPHAN", prov.source_sequence)
            orphan = fill.model_copy(
                update={
                    "snapshot_id": f"fill-{orphan_digest[:12]}",
                    "payload_hash": orphan_digest,
                    "broker_fill_id": "BRK-FILL-ORPHAN",
                    "broker_order_id": "MISSING-ORDER",
                }
            )
            return (fill, orphan)
        return (fill,)

    def trades(self) -> tuple[BrokerFillSnapshot, ...]:
        return self.fills()

    def instrument_metadata(self) -> tuple[InstrumentMapping, ...]:
        base = InstrumentMapping(
            broker_instrument_id="MOCK-TCS",
            security_id="SEC-TCS",
            exchange="NSE",
            trading_symbol="TCS",
            display_symbol="TCS",
            effective_from=_AS_OF,
            mapping_source="mock",
            mapping_confidence="high",
        )
        if self.scenario is MockScenario.MAPPING_AMBIGUITY:
            other = base.model_copy(
                update={
                    "security_id": "SEC-TCS-ALT",
                    "ambiguous": True,
                    "mapping_confidence": "low",
                }
            )
            amb = base.model_copy(update={"ambiguous": True, "mapping_confidence": "low"})
            return (amb, other)
        return (base,)

    def snapshot(self) -> GatewaySnapshotBundle:
        prov = self.session_status()
        account = self.account()
        positions = self.positions()
        holdings = self.holdings()
        margins = self.margins()
        orders = self.orders()
        fills = self.fills()
        mappings = self.instrument_metadata()
        digest = _hash(
            account.payload_hash,
            *(item.payload_hash for item in positions),
            *(item.payload_hash for item in orders),
            *(item.payload_hash for item in fills),
        )
        return GatewaySnapshotBundle(
            bundle_id=f"snap-{digest[:12]}",
            connection_id="conn-mock-1",
            adapter_id=self.adapter_id,
            provenance=prov,
            account=account,
            positions=positions,
            holdings=holdings,
            margins=margins,
            orders=orders,
            fills=fills,
            trades=fills,
            mappings=mappings,
            payload_hash=digest,
        )

    def place_order(self, *_args: object, **_kwargs: object) -> None:
        raise BrokerWriteError("write path disabled; BROKER_WRITE_ENABLED=false")

    def cancel_order(self, *_args: object, **_kwargs: object) -> None:
        raise BrokerWriteError("write path disabled; BROKER_WRITE_ENABLED=false")

    def modify_order(self, *_args: object, **_kwargs: object) -> None:
        raise BrokerWriteError("write path disabled; BROKER_WRITE_ENABLED=false")
