"""Operational control plane. Does not trade, certify, or connect brokers."""

from __future__ import annotations

from quantlab.core.config import LiveSafetyGates
from quantlab.data.fabric.checksums import sha256_bytes
from quantlab.ops.audit import append, flush, writer_healthy
from quantlab.ops.audit import reset_for_tests as reset_audit
from quantlab.ops.backup import reset_for_tests as reset_backup
from quantlab.ops.clock import observe
from quantlab.ops.clock import reset_for_tests as reset_clock
from quantlab.ops.config import bind
from quantlab.ops.environment import current_environment, reject_confusion
from quantlab.ops.health import scorecard, status_from_state
from quantlab.ops.incidents import list_incidents
from quantlab.ops.incidents import record as record_incident
from quantlab.ops.incidents import reset_for_tests as reset_incidents
from quantlab.ops.metrics import reset_for_tests as reset_metrics
from quantlab.ops.models import OpsResult
from quantlab.ops.readiness import readiness_report
from quantlab.ops.repository import last, put
from quantlab.ops.repository import reset_for_tests as reset_repo
from quantlab.ops.resources import assert_disk, inject_free_bytes
from quantlab.ops.resources import reset_for_tests as reset_resources
from quantlab.ops.secrets import reject_live_credentials
from quantlab.ops.secrets import reset_for_tests as reset_secrets
from quantlab.ops.state import FATAL, OpsState, advance_startup, current, force, transition
from quantlab.ops.state import reset_for_tests as reset_state
from quantlab.ops.supervisor import processes
from quantlab.ops.supervisor import reset_for_tests as reset_supervisor
from quantlab.safety.service import last_result as last_safety
from quantlab.safety.state import SafetyState
from quantlab.safety.state import current as safety_state


def reset_for_tests() -> None:
    reset_state()
    reset_supervisor()
    reset_audit()
    reset_backup()
    reset_clock()
    reset_incidents()
    reset_metrics()
    reset_repo()
    reset_resources()
    reset_secrets()
    inject_free_bytes(None)


def _hash(result: OpsResult) -> str:
    material = f"{result.run_id}|{result.state.value}|{result.health.value}|{result.config_hash}"
    return sha256_bytes(material.encode())


def _boot_if_needed() -> None:
    if current() in FATAL:
        return
    guard = 0
    while current() is not OpsState.RUNNING and current() not in FATAL and guard < 16:
        if current() is OpsState.READY:
            transition(OpsState.RUNNING)
            return
        if current() in {OpsState.DEGRADED, OpsState.HALTED, OpsState.RECOVERY}:
            return
        advance_startup()
        guard += 1


def doctor() -> OpsResult:
    reject_live_credentials()
    cfg = bind()
    env = current_environment()
    reject_confusion(declared=env, credentials="research")
    assert_disk(min_free=cfg.disk_min_free_bytes)
    observe(cfg.timestamp)
    _boot_if_needed()
    if last_safety() is not None and safety_state() is SafetyState.HALTED:
        force(OpsState.SAFETY_FAILURE)
        record_incident(kind="safety_halt", detail="safety gateway halted")
    gates = LiveSafetyGates()
    result = OpsResult(
        run_id="ops-doctor",
        state=current(),
        health=status_from_state(),
        readiness=current() is OpsState.RUNNING and writer_healthy(),
        live_trading=gates.live_trading,
        config_hash=cfg.config_hash(),
        environment=env,
        processes=tuple(processes().values()),
        incidents=tuple(list_incidents()),
        extras={"scorecard": scorecard(), "readiness": readiness_report()},
    )
    result = result.model_copy(update={"result_hash": _hash(result)})
    put(result)
    append(result)
    return result


def status() -> OpsResult:
    existing = last()
    return existing if existing is not None else doctor()


def integrate_safety_halt() -> OpsResult:
    force(OpsState.SAFETY_FAILURE)
    record_incident(kind="safety_halt_failure", detail="safety halt integrated")
    return doctor()


def shutdown() -> int:
    return flush()
