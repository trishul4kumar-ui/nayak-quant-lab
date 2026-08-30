"""App-layer ops control plane. Qt cannot start live trading."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from quantlab.core.config import get_settings
from quantlab.core.errors import QuantLabError
from quantlab.ops.audit import history
from quantlab.ops.backup import create as create_backup
from quantlab.ops.backup import get as get_backup
from quantlab.ops.backup import list_backups
from quantlab.ops.backup import verify as verify_backup
from quantlab.ops.checkpoints import write as write_checkpoint
from quantlab.ops.clock import last_seen, observe
from quantlab.ops.config import bind
from quantlab.ops.incidents import list_incidents
from quantlab.ops.recovery import recover
from quantlab.ops.release import current_release
from quantlab.ops.resources import free_bytes
from quantlab.ops.restore import restore as restore_backup
from quantlab.ops.service import doctor, shutdown, status
from quantlab.ops.state import current
from quantlab.ops.supervisor import processes, restart_one, start, stop


def _dump(model: BaseModel) -> dict[str, Any]:
    return model.model_dump(mode="json")


def _safe(fn: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    try:
        return fn()
    except QuantLabError as exc:
        return {"error": str(exc), "live_trading": False}


def status_payload() -> dict[str, Any]:
    result = status()
    return {
        **_dump(result),
        "ops_state": current().value,
        "live_trading": False,
    }


def health_payload() -> dict[str, Any]:
    result = doctor()
    extras = result.extras.get("scorecard", {})
    return {"scorecard": extras, "live_trading": False, "health": result.health.value}


def readiness_payload() -> dict[str, Any]:
    result = status()
    extras = result.extras.get("readiness", {})
    return {**extras, "live_trading": False}


def processes_payload() -> dict[str, Any]:
    return {
        "processes": [_dump(item) for item in processes().values()],
        "live_trading": False,
    }


def start_payload(name: str = "app") -> dict[str, Any]:
    return _dump(start(name))


def stop_payload(name: str = "app") -> dict[str, Any]:
    return _dump(stop(name))


def restart_payload(name: str = "app") -> dict[str, Any]:
    return _dump(restart_one(name))


def incidents_payload() -> dict[str, Any]:
    return {"incidents": [_dump(item) for item in list_incidents()], "live_trading": False}


def backups_payload() -> dict[str, Any]:
    return {"backups": [_dump(item) for item in list_backups()], "live_trading": False}


def backup_payload() -> dict[str, Any]:
    source = Path(get_settings().experiment_ledger_path)
    dest = Path(get_settings().experiment_ledger_path).parent / "ops-backups"
    return _dump(create_backup(source, dest))


def verify_backup_payload(backup_id: str = "") -> dict[str, Any]:
    if not backup_id:
        items = list_backups()
        if not items:
            return {"error": "no backup", "live_trading": False}
        backup_id = items[-1].backup_id
    return _safe(lambda: _dump(verify_backup(backup_id)))


def restore_payload(backup_id: str = "", dest: str = "") -> dict[str, Any]:
    def _run() -> dict[str, Any]:
        target = Path(dest) if dest else Path(get_settings().experiment_ledger_path)
        chosen = backup_id or get_backup(list_backups()[-1].backup_id).backup_id
        path = restore_backup(chosen, target)
        return {"path": str(path), "live_trading": False}

    return _safe(_run)


def recovery_payload() -> dict[str, Any]:
    return _safe(lambda: {"state": recover(explicit=True).value, "live_trading": False})


def checkpoint_payload() -> dict[str, Any]:
    path = Path(get_settings().experiment_ledger_path).parent / "ops-checkpoint.json"
    item = write_checkpoint(
        path,
        checkpoint_id="ops-ckpt-1",
        payload=current().value,
        state=current().value,
    )
    return _dump(item)


def config_payload() -> dict[str, Any]:
    cfg = bind()
    return {**_dump(cfg), "config_hash": cfg.config_hash(), "live_trading": False}


def release_payload() -> dict[str, Any]:
    return _dump(current_release())


def resources_payload() -> dict[str, Any]:
    return {"free_bytes": free_bytes(), "live_trading": False}


def clock_payload() -> dict[str, Any]:
    now = observe(datetime(2024, 1, 2, tzinfo=UTC))
    return {
        "last_seen": last_seen().isoformat(),
        "observed": now.isoformat(),
        "live_trading": False,
    }


def audit_payload() -> dict[str, Any]:
    return {"count": len(history()), "live_trading": False}


def doctor_payload() -> dict[str, Any]:
    return _dump(doctor())


def last_run_row() -> dict[str, Any] | None:
    result = status()
    return {
        "id": result.run_id,
        "state": result.state.value,
        "health": result.health.value,
        "hash": result.result_hash,
        "environment": result.environment.value,
    }


def run_payload() -> dict[str, Any]:
    return doctor_payload()


def shutdown_payload() -> dict[str, Any]:
    return {"flushed": shutdown(), "live_trading": False}
