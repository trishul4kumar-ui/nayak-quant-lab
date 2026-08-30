"""quantlab feature list|inspect|compute|quality."""

from __future__ import annotations

import json
from typing import Any

from quantlab.data.providers.memory import MemoryBarProvider
from quantlab.features.engine import compute_panel, session_calendar
from quantlab.features.quality import summarize_quality
from quantlab.features.registry import get_feature, list_features


def add_feature_parser(sub: Any) -> None:
    parser = sub.add_parser("feature", help="inspect and compute versioned features")
    cmd = parser.add_subparsers(dest="feature_cmd", required=True)
    cmd.add_parser("list", help="list seed-library features")
    inspect_p = cmd.add_parser("inspect", help="print a feature definition")
    inspect_p.add_argument("feature_id")
    compute_p = cmd.add_parser("compute", help="compute a feature on synthetic memory bars")
    compute_p.add_argument("feature_id")
    quality_p = cmd.add_parser("quality", help="feature quality diagnostics")
    quality_p.add_argument("feature_id")


def run_feature_command(args: Any) -> int:
    if args.feature_cmd == "list":
        rows = [
            {
                "feature_id": item.feature_id,
                "version": item.version,
                "family": item.family.value,
                "lookback": item.lookback,
                "lifecycle": item.lifecycle.value,
                "identity": item.identity_hash(),
            }
            for item in list_features()
        ]
        print(json.dumps(rows, indent=2))
        return 0
    definition = get_feature(args.feature_id)
    if args.feature_cmd == "inspect":
        payload = definition.model_dump(mode="json")
        payload["identity_hash"] = definition.identity_hash()
        print(json.dumps(payload, indent=2))
        return 0
    provider = MemoryBarProvider(n_days=80)
    bars = provider.all_bars()
    panel = compute_panel(definition, bars, session_calendar(bars))
    if args.feature_cmd == "compute":
        last = None if not panel else max(panel)
        print(
            json.dumps(
                {
                    "feature_id": definition.feature_id,
                    "identity_hash": definition.identity_hash(),
                    "n_dates": len(panel),
                    "last_as_of": None if last is None else last.isoformat(),
                    "last_cross_section": None if last is None else panel[last],
                    "note": definition.notes or "synthetic bars; not NSE evidence",
                },
                indent=2,
                default=str,
            )
        )
        return 0
    quality = summarize_quality(panel, expected_names=len(provider.get_instruments()))
    print(json.dumps(quality.model_dump(mode="json"), indent=2))
    return 0
