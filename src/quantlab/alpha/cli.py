"""quantlab alpha list|inspect."""

from __future__ import annotations

import json
from typing import Any

from quantlab.alpha.definition import get_alpha, list_alphas


def add_alpha_parser(sub: Any) -> None:
    parser = sub.add_parser("alpha", help="inspect alpha definitions")
    cmd = parser.add_subparsers(dest="alpha_cmd", required=True)
    cmd.add_parser("list", help="list seed alphas")
    inspect_p = cmd.add_parser("inspect", help="print an alpha definition")
    inspect_p.add_argument("alpha_id")


def run_alpha_command(args: Any) -> int:
    if args.alpha_cmd == "list":
        rows = [
            {
                "alpha_id": item.alpha_id,
                "version": item.version,
                "transformation": item.transformation,
                "inputs": item.input_features,
                "horizon": item.horizon,
                "lifecycle": item.lifecycle.value,
            }
            for item in list_alphas()
        ]
        print(json.dumps(rows, indent=2))
        return 0
    print(json.dumps(get_alpha(args.alpha_id).model_dump(mode="json"), indent=2))
    return 0
