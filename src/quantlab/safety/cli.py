"""quantlab safety commands. Gateway only. No broker routing."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from quantlab.app.safety import (
    audit_payload,
    authorize_payload,
    emergency_payload,
    explain_payload,
    gates_payload,
    halt_payload,
    inspect_payload,
    kill_payload,
    policy_payload,
    reconcile_payload,
    recover_payload,
    reject_payload,
    status_payload,
    unkill_payload,
    validate_payload,
)


def add_safety_parser(sub: Any) -> None:
    parser = sub.add_parser("safety", help="live-trading safety gateway (not live, not a broker)")
    cmd = parser.add_subparsers(dest="safety_cmd", required=True)
    cmd.add_parser("status", help="gateway status")
    inspect_p = cmd.add_parser("inspect", help="inspect an evaluation")
    inspect_p.add_argument("item_id", nargs="?", default="last")
    cmd.add_parser("gates", help="G0–G15 results")
    cmd.add_parser("authorize", help="mint non-live authorization (cannot release)")
    cmd.add_parser("reject", help="record a rejection")
    kill_p = cmd.add_parser("kill", help="activate a kill switch")
    kill_p.add_argument("--scope", default="global")
    unkill_p = cmd.add_parser("unkill", help="deactivate a non-live-release kill")
    unkill_p.add_argument("--scope", default="global")
    cmd.add_parser("halt", help="halt new exposure")
    cmd.add_parser("emergency", help="enter emergency")
    cmd.add_parser("recover", help="explicit recovery to SHADOW, not AUTHORIZED")
    cmd.add_parser("reconcile", help="reconciliation barrier")
    cmd.add_parser("audit", help="audit trail")
    cmd.add_parser("policy", help="safety policy identity")
    cmd.add_parser("validate", help="evaluate gates")
    cmd.add_parser("explain", help="explain blocked gates")


def run_safety_command(args: Any) -> int:
    cmd = args.safety_cmd
    item = getattr(args, "item_id", "last")
    scope = getattr(args, "scope", "global")
    mapping: dict[str, Callable[[], Any]] = {
        "status": status_payload,
        "inspect": lambda: inspect_payload(item),
        "gates": gates_payload,
        "authorize": authorize_payload,
        "reject": reject_payload,
        "kill": lambda: kill_payload(scope),
        "unkill": lambda: unkill_payload(scope),
        "halt": halt_payload,
        "emergency": emergency_payload,
        "recover": recover_payload,
        "reconcile": reconcile_payload,
        "audit": audit_payload,
        "policy": policy_payload,
        "validate": validate_payload,
        "explain": explain_payload,
    }
    payload = mapping[cmd]()
    print(json.dumps(payload, indent=2, default=str))
    return 0
