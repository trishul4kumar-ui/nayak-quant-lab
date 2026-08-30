"""In-process snapshot store. Reconnect must not erase history."""

from __future__ import annotations

from threading import Lock

from quantlab.broker_gateway.errors import BrokerGatewayError
from quantlab.broker_gateway.models import GatewayIncident, GatewaySnapshotBundle, ReconResult

_LOCK = Lock()
_BUNDLES: dict[str, GatewaySnapshotBundle] = {}
_LAST: str | None = None
_RECONS: list[ReconResult] = []
_INCIDENTS: list[GatewayIncident] = []
_PAYLOADS: dict[str, str] = {}


def reset_for_tests() -> None:
    global _LAST
    with _LOCK:
        _BUNDLES.clear()
        _RECONS.clear()
        _INCIDENTS.clear()
        _PAYLOADS.clear()
        _LAST = None


def put_bundle(bundle: GatewaySnapshotBundle) -> GatewaySnapshotBundle:
    global _LAST
    with _LOCK:
        prior = _PAYLOADS.get(bundle.bundle_id)
        if prior is not None and prior != bundle.payload_hash:
            raise BrokerGatewayError("external event collision: same identity, different payload")
        _PAYLOADS[bundle.bundle_id] = bundle.payload_hash
        _BUNDLES[bundle.bundle_id] = bundle
        _LAST = bundle.bundle_id
        return bundle


def last_bundle() -> GatewaySnapshotBundle | None:
    if _LAST is None:
        return None
    return _BUNDLES.get(_LAST)


def get_bundle(item_id: str) -> GatewaySnapshotBundle | None:
    if item_id in {"", "last"}:
        return last_bundle()
    return _BUNDLES.get(item_id)


def list_bundles() -> list[GatewaySnapshotBundle]:
    return list(_BUNDLES.values())


def put_recon(result: ReconResult) -> ReconResult:
    with _LOCK:
        _RECONS.append(result)
        return result


def list_recons() -> list[ReconResult]:
    return list(_RECONS)


def last_recon() -> ReconResult | None:
    return _RECONS[-1] if _RECONS else None


def put_incident(item: GatewayIncident) -> GatewayIncident:
    with _LOCK:
        _INCIDENTS.append(item)
        return item


def list_incidents() -> list[GatewayIncident]:
    return list(_INCIDENTS)
