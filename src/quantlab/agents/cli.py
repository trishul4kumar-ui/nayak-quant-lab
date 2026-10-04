from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime

from quantlab.agents.contracts import AgentRole, AgentRunRecord
from quantlab.agents.permissions import mandate_for
from quantlab.agents.provider import configured_provider
from quantlab.agents.repository import AgentRepository
from quantlab.agents.tool_gateway import AgentToolGateway
from quantlab.ai.permissions import DENIED_CAPABILITIES
from quantlab.control_plane.sqlite import ControlPlaneStoreError


def add_agents_parser(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = sub.add_parser("agents", help="AI quant desk research contracts and audit")
    parser.add_argument(
        "agents_action",
        choices=(
            "status",
            "permissions",
            "tools",
            "audit",
            "provider-health",
        ),
    )
    parser.add_argument("--run-id")


def run_agents_command(args: argparse.Namespace) -> int:
    try:
        return _run_agents_command(args)
    except (ControlPlaneStoreError, ValueError, KeyError):
        print(json.dumps({"error": "AGENT_PERSISTENCE_UNAVAILABLE", "live_trading": False}))
        return 2


def _run_agents_command(args: argparse.Namespace) -> int:
    repository = AgentRepository()
    try:
        provider = configured_provider()
        mandate = mandate_for(AgentRole.BULL, created_at=datetime(2026, 10, 4, tzinfo=UTC))
        if args.agents_action == "provider-health":
            payload: object = provider.health().model_dump(mode="json")
        elif args.agents_action == "permissions":
            payload = {
                "allowed": sorted(mandate.granted),
                "always_denied": sorted(DENIED_CAPABILITIES),
            }
        elif args.agents_action == "tools":
            payload = [
                {"tool": tool, "capability": capability, "adapter_bound": bound}
                for tool, capability, bound in AgentToolGateway(repository, mandate).catalog()
            ]
        elif args.agents_action == "audit":
            payload = [row.model_dump(mode="json") for row in repository.audit_events(args.run_id)]
        else:
            payload = {
                "runs": len(repository.list(AgentRunRecord)),
                "provider": provider.health().model_dump(mode="json"),
                "live_trading": False,
                "ai_live_order_authority": False,
            }
        print(json.dumps(payload, indent=2))
        return 0
    finally:
        repository.close()
