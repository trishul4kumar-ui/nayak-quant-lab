"""quantlab certification — live-trading promotion gate. Not Prompt 23 validation."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from quantlab.app.release import (
    approve_payload,
    audit_payload,
    certify_payload,
    create_payload,
    evidence_payload,
    expire_payload,
    inspect_payload,
    lineage_payload,
    list_payload,
    manifest_payload,
    readiness_payload,
    reject_payload,
    report_payload,
    review_payload,
    revoke_payload,
    status_payload,
    suspend_payload,
    validate_payload,
    waivers_payload,
)


def add_certification_parser(sub: Any) -> None:
    parser = sub.add_parser(
        "certification",
        help="live-trading certification / promotion / release gate (not live)",
    )
    cmd = parser.add_subparsers(dest="certification_cmd", required=True)
    cmd.add_parser("list", help="list packages")
    inspect_p = cmd.add_parser("inspect", help="inspect a package")
    inspect_p.add_argument("item_id", nargs="?", default="last")
    cmd.add_parser("create", help="create a draft package")
    cmd.add_parser("evidence", help="evidence matrix")
    cmd.add_parser("validate", help="evaluate domains")
    cmd.add_parser("review", help="certification review status")
    cmd.add_parser("approve", help="human release eligibility (not live)")
    cmd.add_parser("reject", help="reject a package")
    cmd.add_parser("certify", help="certify when criteria pass (not live)")
    cmd.add_parser("status", help="gate status")
    cmd.add_parser("audit", help="audit trail")
    cmd.add_parser("expire", help="expire certification")
    cmd.add_parser("suspend", help="suspend certification")
    cmd.add_parser("revoke", help="revoke certification")
    cmd.add_parser("waivers", help="list waivers")
    cmd.add_parser("manifest", help="release manifest")
    cmd.add_parser("report", help="certification report")
    cmd.add_parser("lineage", help="retained attempts")
    cmd.add_parser("readiness", help="blocked criteria")


def add_research_release_parsers(research_sub: Any) -> None:
    for name, help_text in (
        ("live-certification", "live-trading certification gate (not Prompt 23)"),
        ("live-readiness", "release readiness scorecard"),
        ("promotion", "promotion / release eligibility"),
        ("release-gate", "release gate (not live enablement)"),
        ("certification-audit", "live-certification audit"),
    ):
        item = research_sub.add_parser(name, help=help_text)
        item.add_argument("item_id", nargs="?", default="last")
        item.add_argument("--ledger", default="")


def run_certification_command(args: Any) -> int:
    cmd = args.certification_cmd
    item = getattr(args, "item_id", "last")
    mapping: dict[str, Callable[[], Any]] = {
        "list": list_payload,
        "inspect": lambda: inspect_payload(item),
        "create": create_payload,
        "evidence": evidence_payload,
        "validate": validate_payload,
        "review": review_payload,
        "approve": approve_payload,
        "reject": reject_payload,
        "certify": certify_payload,
        "status": status_payload,
        "audit": audit_payload,
        "expire": expire_payload,
        "suspend": suspend_payload,
        "revoke": revoke_payload,
        "waivers": waivers_payload,
        "manifest": manifest_payload,
        "report": report_payload,
        "lineage": lineage_payload,
        "readiness": readiness_payload,
    }
    print(json.dumps(mapping[cmd](), indent=2, default=str))
    return 0


def run_research_release_command(args: Any) -> int:
    item = getattr(args, "item_id", "last")
    cmd = args.research_cmd
    if cmd in {"live-certification", "promotion", "release-gate"}:
        payload: Any = inspect_payload(item)
    elif cmd == "live-readiness":
        payload = readiness_payload()
    else:
        payload = audit_payload()
    print(json.dumps(payload, indent=2, default=str))
    return 0
