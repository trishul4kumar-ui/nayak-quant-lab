"""Read-only daily desk inspection commands."""

from __future__ import annotations

import argparse
import json

from quantlab.agent_desk.repository import DailyDeskRepository
from quantlab.control_plane.sqlite import ControlPlaneStoreError


def add_agent_desk_parser(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = sub.add_parser("daily-desk", help="inspect persisted research-only daily desk state")
    command = parser.add_subparsers(dest="daily_desk_action", required=True)
    command.add_parser("status", help="show latest immutable daily desk state")


def run_agent_desk_command(args: argparse.Namespace) -> int:
    try:
        repository = DailyDeskRepository()
        try:
            states = repository.states()
            print(json.dumps([item.model_dump(mode="json") for item in states[-100:]], indent=2))
            return 0
        finally:
            repository.close()
    except (ControlPlaneStoreError, OSError, RuntimeError, ValueError, KeyError):
        print(json.dumps({"error": "DAILY_DESK_PERSISTENCE_UNAVAILABLE", "live_trading": False}))
        return 2
