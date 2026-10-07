"""Persistent system status. UI displays this model; it does not invent strings."""

from __future__ import annotations

from pydantic import BaseModel

from quantlab.app.health import ComponentStatus, HealthReport
from quantlab.app.mode import AppMode
from quantlab.broker_gateway.state import current as broker_state
from quantlab.core.config import LiveSafetyGates
from quantlab.risk.states import RiskState


class SystemStatus(BaseModel):
    system: str
    data: str
    research: str
    risk: str
    execution: str
    broker: str
    live_trading: str
    mode: AppMode
    risk_state: RiskState = RiskState.NORMAL

    @classmethod
    def from_health(
        cls,
        report: HealthReport,
        gates: LiveSafetyGates,
        risk_state: RiskState = RiskState.NORMAL,
    ) -> SystemStatus:
        def label(name: str, fallback: str) -> str:
            component = report.by_name(name)
            if component is None:
                return fallback
            if component.status is ComponentStatus.OK:
                return "READY"
            if component.status is ComponentStatus.OPTIONAL:
                return "OFFLINE"
            return "FAILED"

        system = "HEALTHY" if report.research_ready() else "DEGRADED"
        live = "DISABLED" if not gates.live_trading else "ENABLED"
        broker = broker_state().value.upper().replace("_", " ")
        return cls(
            system=system,
            data=label("data_store", "READY"),
            research=label("research_engine", "READY"),
            risk="ARMED" if gates.risk_engine_healthy else "UNHEALTHY",
            execution=label("execution_engine", "READY"),
            broker=broker,
            live_trading=live,
            mode=report.mode,
            risk_state=risk_state,
        )
