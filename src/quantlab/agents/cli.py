from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from quantlab.agents.bear import BearWorker, bear_mandate, create_bear_context, search_bear_history
from quantlab.agents.bull import BullWorker, bull_mandate, create_bull_context, search_bull_history
from quantlab.agents.contracts import AgentRunRecord, AgentState, ResearchMode
from quantlab.agents.inputs import read_history, read_snapshot
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
            "run-bull",
            "bull-history",
            "run-bear",
            "bear-history",
        ),
    )
    parser.add_argument("--run-id")
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--history", type=Path)
    parser.add_argument("--replay", action="store_true")
    parser.add_argument("--query", default="")


def run_agents_command(args: argparse.Namespace) -> int:
    try:
        return _run_agents_command(args)
    except ControlPlaneStoreError:
        print(json.dumps({"error": "AGENT_PERSISTENCE_UNAVAILABLE", "live_trading": False}))
        return 2
    except (OSError, RuntimeError, ValueError, KeyError):
        print(json.dumps({"error": "AGENT_INPUT_OR_RUN_BLOCKED", "live_trading": False}))
        return 2


def _run_agents_command(args: argparse.Namespace) -> int:
    repository = AgentRepository()
    exit_code = 0
    try:
        provider = configured_provider()
        mandate = bull_mandate(datetime(2026, 10, 4, tzinfo=UTC))
        if args.agents_action in {"run-bull", "run-bear"}:
            if args.snapshot is None:
                raise ValueError("EXPLICIT_SNAPSHOT_REQUIRED")
            snapshot = read_snapshot(args.snapshot)
            now = datetime.now(UTC)
            history = read_history(args.history, snapshot, now) if args.history else None
            factory = (
                create_bull_context if args.agents_action == "run-bull" else create_bear_context
            )
            context = factory(
                repository,
                snapshot,
                provider,
                now=now,
                history=history,
                mode=ResearchMode.REPLAY if args.replay else ResearchMode.RESEARCH,
            )
            worker = BullWorker if args.agents_action == "run-bull" else BearWorker
            run = worker(repository, provider).run(context)
            payload: object = run.model_dump(mode="json")
            if run.state in {AgentState.BLOCKED, AgentState.STALE, AgentState.ERROR}:
                exit_code = 2
        elif args.agents_action in {"bull-history", "bear-history"}:
            search = (
                search_bull_history if args.agents_action == "bull-history" else search_bear_history
            )
            payload = [
                memo.model_dump(mode="json") for memo in search(repository, args.query)[-100:]
            ]
        elif args.agents_action == "provider-health":
            payload = provider.health().model_dump(mode="json")
        elif args.agents_action == "permissions":
            payload = {
                "allowed": sorted(mandate.granted),
                "bear_allowed": sorted(bear_mandate(mandate.created_at).granted),
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
        return exit_code
    finally:
        repository.close()
