"""Read-only candidate inspection commands; no order or sizing parameters exist."""

from __future__ import annotations

import argparse
import json

from quantlab.control_plane.sqlite import ControlPlaneStoreError
from quantlab.trade_candidates.ranking import rank_for_review
from quantlab.trade_candidates.repository import CandidateRepository


def add_candidates_parser(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = sub.add_parser("candidates", help="research-only trade candidate packet inspection")
    cmd = parser.add_subparsers(dest="candidates_action", required=True)
    cmd.add_parser("history", help="list immutable candidate packets")
    inspect = cmd.add_parser("inspect", help="inspect a candidate by artifact hash")
    inspect.add_argument("candidate_hash")


def run_candidates_command(args: argparse.Namespace) -> int:
    try:
        repository = CandidateRepository()
        try:
            candidates = rank_for_review(repository.list())
            if args.candidates_action == "history":
                print(
                    json.dumps(
                        [candidate.model_dump(mode="json") for candidate in candidates[-100:]],
                        indent=2,
                    )
                )
                return 0
            payload = next(
                (
                    candidate.model_dump(mode="json")
                    for candidate in candidates
                    if candidate.content_hash == args.candidate_hash
                ),
                None,
            )
            if payload is None:
                raise KeyError("candidate missing")
            print(json.dumps(payload, indent=2))
            return 0
        finally:
            repository.close()
    except (ControlPlaneStoreError, OSError, RuntimeError, ValueError, KeyError):
        print(json.dumps({"error": "CANDIDATE_PERSISTENCE_UNAVAILABLE", "live_trading": False}))
        return 2
