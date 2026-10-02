"""Command-line readout for Live Operations; no command resumes or trades."""
# ruff: noqa: E501

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from quantlab.live_ops.models import IncidentEvidence
from quantlab.live_ops.repository import actions, alerts, incident_by_id, incidents, last_snapshot
from quantlab.live_ops.service import LiveOperationsService
from quantlab.realtime_data.hashing import sha256


def add_live_ops_parser(sub: Any) -> None:
    parser = sub.add_parser(
        "live-ops", help="live operations monitoring and incident response (no execution)"
    )
    cmd = parser.add_subparsers(dest="live_ops_cmd", required=True)
    for name in ("status", "health", "alerts", "incidents", "audit"):
        cmd.add_parser(name)
    incident = cmd.add_parser("incident")
    incident_cmd = incident.add_subparsers(dest="incident_cmd", required=True)
    show = incident_cmd.add_parser("show")
    show.add_argument("incident_id")
    acknowledge = incident_cmd.add_parser("acknowledge")
    acknowledge.add_argument("incident_id")
    acknowledge.add_argument("--actor", required=True)
    acknowledge.add_argument("--rationale", required=True)
    resolve = incident_cmd.add_parser("resolve")
    resolve.add_argument("incident_id")
    resolve.add_argument("--actor", required=True)
    resolve.add_argument("--rationale", required=True)
    resolve.add_argument("--evidence", required=True)


def run_live_ops_command(args: Any) -> int:
    service = LiveOperationsService()
    cmd = args.live_ops_cmd
    if cmd == "incident":
        cmd = f"incident-{args.incident_cmd}"
    if cmd in {"status", "health"}:
        snapshot = service.collect()
        payload: Any = snapshot if cmd == "status" else snapshot.signals
    elif cmd == "alerts":
        payload = alerts()
    elif cmd == "incidents":
        payload = incidents()
    elif cmd == "audit":
        payload = {"alerts": alerts(), "incidents": incidents(), "actions": actions()}
    elif cmd == "incident-show":
        payload = incident_by_id(args.incident_id)
        if payload is None:
            print(json.dumps({"error": "incident not found"}, indent=2))
            return 1
    elif cmd == "incident-acknowledge":
        payload = service.acknowledge(
            args.incident_id, actor_id=args.actor, rationale=args.rationale
        )
    else:
        latest = last_snapshot()
        evidence = IncidentEvidence(
            evidence_id=f"human-evidence-{sha256(args.evidence)[:12]}",
            source="human",
            content_hash=sha256(args.evidence),
            observed_at=latest.captured_at if latest else datetime.now(tz=UTC),
            detail=args.evidence,
        )
        payload = service.resolve(
            args.incident_id,
            actor_id=args.actor,
            rationale=args.rationale,
            evidence=(evidence,),
            condition_persists=False,
        )
    if isinstance(payload, (tuple, list)):
        rendered = [item.model_dump(mode="json") for item in payload]
    else:
        rendered = payload.model_dump(mode="json") if hasattr(payload, "model_dump") else payload
    print(json.dumps(rendered, indent=2, default=str))
    return 0
