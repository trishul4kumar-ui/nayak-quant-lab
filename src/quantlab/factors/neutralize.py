"""Residualize a factor against controls. Residual identity is a new version."""

from __future__ import annotations

from quantlab.alpha.combinations import residualize
from quantlab.core.errors import FactorError
from quantlab.factors.definition import FactorDefinition, FactorSource
from quantlab.features.engine import Panel


def residual_factor_definition(
    target: FactorDefinition,
    controls: list[FactorDefinition],
) -> FactorDefinition:
    control_ids = ",".join(item.factor_id for item in controls)
    return target.model_copy(
        update={
            "factor_id": f"{target.factor_id}_resid_{'_'.join(c.factor_id for c in controls)}",
            "version": "1",
            "name": f"{target.name} residual of {control_ids}",
            "mathematical_definition": (
                f"CS residual of {target.factor_id} on [{control_ids}] plus intercept"
            ),
            "source": FactorSource.RESIDUAL,
            "lineage": {
                **target.lineage,
                "residual_of": target.factor_id,
                "controls": control_ids,
            },
            "notes": "Residual factor is a new identity; the original factor is not overwritten",
        }
    )


def residualize_panel(target: Panel, control: Panel) -> Panel:
    out: Panel = {}
    for as_of, row in target.items():
        other = control.get(as_of)
        if other is None:
            continue
        resid = residualize(row, other)
        if resid is None:
            continue
        out[as_of] = resid
    if not out:
        raise FactorError("residualization produced an empty panel")
    return out
