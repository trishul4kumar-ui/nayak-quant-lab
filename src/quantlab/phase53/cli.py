"""Read-only CLI for the Phase 53 evidence dossier."""

from __future__ import annotations

import json
from typing import Any

from quantlab.phase53.service import assess_current_state


def add_phase53_parser(sub: Any) -> None:
    parser = sub.add_parser(
        "phase53",
        help="read-only Phase 53 go/no-go evidence; cannot enable trading",
    )
    parser.add_subparsers(dest="phase53_cmd", required=True).add_parser(
        "status", help="assess currently recorded evidence without changing execution settings"
    )


def run_phase53_command(args: Any) -> int:
    if args.phase53_cmd != "status":
        raise ValueError(f"unsupported Phase 53 command: {args.phase53_cmd}")
    print(json.dumps(assess_current_state().model_dump(mode="json"), indent=2, default=str))
    return 0
