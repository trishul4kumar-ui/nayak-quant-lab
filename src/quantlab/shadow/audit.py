"""Incidents are retained. None may be silently deleted."""

from __future__ import annotations

from datetime import UTC, datetime

from quantlab.shadow.enums import IncidentKind, IncidentSeverity
from quantlab.shadow.models import ShadowIncident
from quantlab.shadow.state import add_incident, list_incidents


def record_incident(
    kind: IncidentKind,
    description: str,
    *,
    severity: IncidentSeverity = IncidentSeverity.HIGH,
    source: str = "shadow",
    cycle_id: str = "",
) -> ShadowIncident:
    item = ShadowIncident(
        incident_id=f"INC-{kind.value}-{cycle_id or 'na'}",
        timestamp=datetime(2024, 1, 15, tzinfo=UTC),
        severity=severity,
        source=source,
        kind=kind,
        description=description,
        lineage={"cycle_id": cycle_id} if cycle_id else {},
    )
    return add_incident(item)


def incidents() -> list[ShadowIncident]:
    return list_incidents()
