"""Research-only CLI for frozen level plans. It accepts no order or size arguments."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from quantlab.control_plane.sqlite import ControlPlaneStoreError
from quantlab.trade_levels.engine import chart_overlay
from quantlab.trade_levels.models import TradeLevelInput
from quantlab.trade_levels.repository import TradeLevelRepository


def add_trade_levels_parser(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = sub.add_parser("trade-levels", help="deterministic, research-only level plans")
    cmd = parser.add_subparsers(dest="trade_levels_action", required=True)
    compute = cmd.add_parser("compute", help="freeze a level plan from verified JSON input")
    compute.add_argument("--input", required=True, type=Path)
    inspect = cmd.add_parser("inspect", help="inspect a frozen level plan")
    inspect.add_argument("plan_hash")
    cmd.add_parser("history", help="list frozen level plans")


def run_trade_levels_command(args: argparse.Namespace) -> int:
    try:
        return _run_trade_levels_command(args)
    except (ControlPlaneStoreError, OSError, RuntimeError, ValueError, KeyError):
        print(
            json.dumps(
                {"error": "TRADE_LEVEL_INPUT_OR_PERSISTENCE_BLOCKED", "live_trading": False}
            )
        )
        return 2


def _run_trade_levels_command(args: argparse.Namespace) -> int:
    repository = TradeLevelRepository()
    try:
        if args.trade_levels_action == "compute":
            value = TradeLevelInput.model_validate_json(args.input.read_text())
            plan = repository.compute(value, now=datetime.now(UTC))
            print(
                json.dumps(
                    {
                        "plan": plan.model_dump(mode="json"),
                        "overlay": chart_overlay(plan).model_dump(mode="json"),
                    },
                    indent=2,
                )
            )
            return 2 if plan.status.value == "NO_VALID_ENTRY" else 0
        if args.trade_levels_action == "inspect":
            plan = repository.get(args.plan_hash)
            print(json.dumps(plan.model_dump(mode="json"), indent=2))
            return 2 if plan.status.value == "NO_VALID_ENTRY" else 0
        print(
            json.dumps(
                [plan.model_dump(mode="json") for plan in repository.list()[-100:]], indent=2
            )
        )
        return 0
    finally:
        repository.close()
