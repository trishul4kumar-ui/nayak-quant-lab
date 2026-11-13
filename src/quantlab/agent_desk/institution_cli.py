"""Explicit frozen-input entry point for the institutional research desk."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from quantlab.agent_desk.institution import DeskCycle, InstitutionDeskService, InstitutionDocument
from quantlab.agents.inputs import read_history, read_snapshot
from quantlab.agents.provider import configured_provider
from quantlab.agents.repository import AgentRepository


def add_institution_parser(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = sub.add_parser("institution", help="local NAYAK institutional research desk")
    parser.add_argument("action", choices=("run", "history", "ask"))
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--history", type=Path)
    parser.add_argument("--documents", type=Path)
    parser.add_argument("--replay", action="store_true")
    parser.add_argument("--cycle")
    parser.add_argument("--question")


def run_institution_command(args: argparse.Namespace) -> int:
    repository: AgentRepository | None = None
    try:
        repository = AgentRepository()
        service = InstitutionDeskService(repository, configured_provider())
        now = datetime.now(UTC)
        if args.action == "history":
            payload: object = [
                service.verify(cycle).model_dump(mode="json")
                for cycle in repository.list(DeskCycle)[-50:]
            ]
        elif args.action == "ask":
            if not args.cycle or not args.question:
                raise ValueError("explicit cycle and question required")
            payload = service.ask(args.cycle, args.question, now=now).model_dump(mode="json")
        else:
            if args.snapshot is None:
                raise ValueError("explicit snapshot required")
            snapshot = read_snapshot(args.snapshot)
            history = read_history(args.history, snapshot, now) if args.history else None
            documents: tuple[InstitutionDocument, ...] = ()
            if args.documents:
                if args.documents.stat().st_size > 200_000:
                    raise ValueError("document input too large")
                rows = json.loads(args.documents.read_bytes())
                if not isinstance(rows, list) or not 1 <= len(rows) <= 8:
                    raise ValueError("bounded document list required")
                documents = tuple(InstitutionDocument.model_validate(row) for row in rows)
            payload = service.run(
                snapshot, now=now, replay=args.replay, history=history, documents=documents
            ).model_dump(mode="json")
        print(json.dumps(payload, indent=2))
        return 0
    except (OSError, ValueError, RuntimeError, KeyError):
        print(
            json.dumps({"error": "INSTITUTION_INPUT_OR_RUN_BLOCKED", "execution_authority": False})
        )
        return 2
    finally:
        if repository is not None:
            repository.close()
