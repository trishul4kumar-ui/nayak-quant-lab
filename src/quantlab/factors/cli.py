"""quantlab factor list|inspect|compute|exposure."""

from __future__ import annotations

import json
from typing import Any

from quantlab.core.config import get_settings
from quantlab.data.providers.memory import MemoryBarProvider
from quantlab.factors.engine import compute_factor_panel
from quantlab.factors.exposure import exposure_matrix, portfolio_exposures
from quantlab.factors.registry import get_factor, list_factors
from quantlab.features.engine import session_calendar
from quantlab.portfolio.baselines import equal_weight_names, targets_to_map
from quantlab.portfolio.spec import get_portfolio_model


def add_factor_parser(sub: Any) -> None:
    parser = sub.add_parser("factor", help="inspect and compute versioned factors")
    cmd = parser.add_subparsers(dest="factor_cmd", required=True)
    cmd.add_parser("list", help="list seed-library factors")
    inspect_p = cmd.add_parser("inspect", help="print a factor definition")
    inspect_p.add_argument("factor_id")
    compute_p = cmd.add_parser("compute", help="compute a factor on synthetic memory bars")
    compute_p.add_argument("factor_id")
    exposure_p = cmd.add_parser("exposure", help="portfolio factor exposures on synthetic bars")
    exposure_p.add_argument("portfolio")


def run_factor_command(args: Any) -> int:
    if args.factor_cmd == "list":
        rows = [
            {
                "factor_id": item.factor_id,
                "version": item.version,
                "category": item.category.value,
                "source": item.source.value,
                "lifecycle": item.lifecycle.value,
                "identity": item.identity_hash(),
            }
            for item in list_factors()
        ]
        print(json.dumps(rows, indent=2))
        return 0
    if args.factor_cmd == "inspect":
        definition = get_factor(args.factor_id)
        payload = definition.model_dump(mode="json")
        payload["identity_hash"] = definition.identity_hash()
        print(json.dumps(payload, indent=2))
        return 0
    if args.factor_cmd == "compute":
        definition = get_factor(args.factor_id)
        provider = MemoryBarProvider(n_days=80)
        bars = provider.all_bars()
        panel, observation = compute_factor_panel(definition, bars, session_calendar(bars))
        last = None if not panel else max(panel)
        print(
            json.dumps(
                {
                    "factor_id": definition.factor_id,
                    "identity_hash": definition.identity_hash(),
                    "status": observation.status.value,
                    "n_dates": len(panel),
                    "last_as_of": None if last is None else last.isoformat(),
                    "last_cross_section": None if last is None else panel[last],
                    "note": observation.note or definition.notes,
                },
                indent=2,
                default=str,
            )
        )
        return 0
    return _exposure(args.portfolio)


def _exposure(portfolio_id: str) -> int:
    try:
        model = get_portfolio_model(portfolio_id)
        note = f"equal-weight snapshot for {model.portfolio_id}; not an order"
    except KeyError:
        note = f"unknown portfolio {portfolio_id}; equal-weight universe snapshot"
    provider = MemoryBarProvider(n_days=80)
    bars = provider.all_bars()
    dates = session_calendar(bars)
    as_of = dates[-1]
    names = [str(inst) for inst in bars]
    weights = targets_to_map(equal_weight_names({name: 1.0 for name in names}))
    panels = {}
    for item in list_factors():
        if item.source.value == "not_implemented":
            continue
        panel, obs = compute_factor_panel(item, bars, dates)
        if obs.status.value != "not_tested" and panel:
            panels[item.factor_id] = panel
    matrix = exposure_matrix(panels, as_of)
    report = portfolio_exposures(weights, matrix)
    print(
        json.dumps(
            {
                "portfolio": portfolio_id,
                "as_of": as_of.isoformat(),
                "exposures": report.exposures,
                "missing": report.missing,
                "status": report.status.value,
                "note": note,
                "settings_ledger": get_settings().experiment_ledger_path,
            },
            indent=2,
            default=str,
        )
    )
    return 0
