"""Broker-neutral read-only adapter protocol. No order placement."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

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
    Provenance,
)


@runtime_checkable
class BrokerAdapter(Protocol):
    adapter_id: str
    broker: str

    def connect(self) -> BrokerHealth: ...

    def disconnect(self) -> BrokerHealth: ...

    def health(self) -> BrokerHealth: ...

    def account(self) -> BrokerAccountSnapshot: ...

    def positions(self) -> tuple[BrokerPositionSnapshot, ...]: ...

    def holdings(self) -> tuple[BrokerHoldingSnapshot, ...]: ...

    def margins(self) -> BrokerMarginSnapshot: ...

    def orders(self) -> tuple[BrokerOrderSnapshot, ...]: ...

    def fills(self) -> tuple[BrokerFillSnapshot, ...]: ...

    def trades(self) -> tuple[BrokerFillSnapshot, ...]: ...

    def instrument_metadata(self) -> tuple[InstrumentMapping, ...]: ...

    def session_status(self) -> Provenance: ...

    def snapshot(self) -> GatewaySnapshotBundle: ...
