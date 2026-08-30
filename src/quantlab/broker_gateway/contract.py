"""Vendor read-only contract. Not enabled. No SDK import."""

from __future__ import annotations

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
    Provenance,
)


class VendorReadOnlyContract:
    """Placeholder for a future vendor session. Raises until explicitly enabled."""

    adapter_id = "vendor-readonly-contract"
    broker = "vendor"

    def connect(self) -> BrokerHealth:
        raise BrokerGatewayError("vendor read-only adapter is not enabled")

    def disconnect(self) -> BrokerHealth:
        raise BrokerGatewayError("vendor read-only adapter is not enabled")

    def health(self) -> BrokerHealth:
        raise BrokerGatewayError("vendor read-only adapter is not enabled")

    def account(self) -> BrokerAccountSnapshot:
        raise BrokerGatewayError("vendor read-only adapter is not enabled")

    def positions(self) -> tuple[BrokerPositionSnapshot, ...]:
        raise BrokerGatewayError("vendor read-only adapter is not enabled")

    def holdings(self) -> tuple[BrokerHoldingSnapshot, ...]:
        raise BrokerGatewayError("vendor read-only adapter is not enabled")

    def margins(self) -> BrokerMarginSnapshot:
        raise BrokerGatewayError("vendor read-only adapter is not enabled")

    def orders(self) -> tuple[BrokerOrderSnapshot, ...]:
        raise BrokerGatewayError("vendor read-only adapter is not enabled")

    def fills(self) -> tuple[BrokerFillSnapshot, ...]:
        raise BrokerGatewayError("vendor read-only adapter is not enabled")

    def trades(self) -> tuple[BrokerFillSnapshot, ...]:
        raise BrokerGatewayError("vendor read-only adapter is not enabled")

    def instrument_metadata(self) -> tuple[InstrumentMapping, ...]:
        raise BrokerGatewayError("vendor read-only adapter is not enabled")

    def session_status(self) -> Provenance:
        raise BrokerGatewayError("vendor read-only adapter is not enabled")

    def snapshot(self) -> GatewaySnapshotBundle:
        raise BrokerGatewayError("vendor read-only adapter is not enabled")

    def place_order(self, *_args: object, **_kwargs: object) -> None:
        raise BrokerWriteError("write path disabled; BROKER_WRITE_ENABLED=false")
