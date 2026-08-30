"""quantlab ops commands. Control plane only. No live trading."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from quantlab.app.ops import (
    audit_payload,
    backup_payload,
    backups_payload,
    checkpoint_payload,
    clock_payload,
    config_payload,
    doctor_payload,
    health_payload,
    incidents_payload,
    processes_payload,
    readiness_payload,
    recovery_payload,
    release_payload,
    resources_payload,
    restart_payload,
    restore_payload,
    start_payload,
    status_payload,
    stop_payload,
    verify_backup_payload,
)


def add_ops_parser(sub: Any) -> None:
    parser = sub.add_parser("ops", help="production operational control plane (not live)")
    cmd = parser.add_subparsers(dest="ops_cmd", required=True)
    cmd.add_parser("status", help="system status")
    cmd.add_parser("health", help="health scorecard")
    cmd.add_parser("readiness", help="readiness / liveness")
    cmd.add_parser("processes", help="logical processes")
    start_p = cmd.add_parser("start", help="start a logical process")
    start_p.add_argument("name", nargs="?", default="app")
    stop_p = cmd.add_parser("stop", help="stop a logical process")
    stop_p.add_argument("name", nargs="?", default="app")
    restart_p = cmd.add_parser("restart", help="restart a logical process")
    restart_p.add_argument("name", nargs="?", default="app")
    cmd.add_parser("incidents", help="ops incidents")
    cmd.add_parser("backups", help="list backups")
    cmd.add_parser("backup", help="create a checksummed backup")
    verify_p = cmd.add_parser("verify-backup", help="verify backup checksum")
    verify_p.add_argument("backup_id", nargs="?", default="")
    restore_p = cmd.add_parser("restore", help="restore a verified backup")
    restore_p.add_argument("backup_id", nargs="?", default="")
    restore_p.add_argument("--dest", default="")
    cmd.add_parser("recovery", help="explicit recovery")
    cmd.add_parser("checkpoint", help="write ops checkpoint")
    cmd.add_parser("config", help="config identity")
    cmd.add_parser("release", help="release identity")
    cmd.add_parser("resources", help="disk / resources")
    cmd.add_parser("clock", help="clock integrity")
    cmd.add_parser("audit", help="audit buffer")
    cmd.add_parser("doctor", help="run ops doctor")


def run_ops_command(args: Any) -> int:
    cmd = args.ops_cmd
    name = getattr(args, "name", "app")
    backup_id = getattr(args, "backup_id", "")
    dest = getattr(args, "dest", "")
    mapping: dict[str, Callable[[], Any]] = {
        "status": status_payload,
        "health": health_payload,
        "readiness": readiness_payload,
        "processes": processes_payload,
        "start": lambda: start_payload(name),
        "stop": lambda: stop_payload(name),
        "restart": lambda: restart_payload(name),
        "incidents": incidents_payload,
        "backups": backups_payload,
        "backup": backup_payload,
        "verify-backup": lambda: verify_backup_payload(backup_id),
        "restore": lambda: restore_payload(backup_id, dest),
        "recovery": recovery_payload,
        "checkpoint": checkpoint_payload,
        "config": config_payload,
        "release": release_payload,
        "resources": resources_payload,
        "clock": clock_payload,
        "audit": audit_payload,
        "doctor": doctor_payload,
    }
    print(json.dumps(mapping[cmd](), indent=2, default=str))
    return 0
