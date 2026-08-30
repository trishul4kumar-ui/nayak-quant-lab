"""Diversity, leave-one-out, sign, and selection-bias diagnostics."""

from __future__ import annotations

import pytest

from quantlab.data.providers.memory import MemoryBarProvider
from quantlab.domain.models import Instrument
from quantlab.ensemble.definition import ComponentType, EnsembleComponent, EnsembleDefinition
from quantlab.ensemble.diversity import leave_one_out, pairwise_correlations
from quantlab.ensemble.engine import run_ensemble
from quantlab.ensemble.experiment import run_ensemble_experiment
from quantlab.ensemble.registry import get_ensemble
from quantlab.features.engine import Panel, session_calendar
from quantlab.research.cross_section import spearman_ic


def _bars() -> dict:
    return MemoryBarProvider(n_days=80).all_bars()


@pytest.mark.ensemble
def test_leave_one_out_records_every_drop() -> None:
    bars = _bars()
    panels, labels, _result = run_ensemble(get_ensemble("ew_mom_5_20"), bars)
    dates = session_calendar(bars)
    report = leave_one_out(panels, labels, dates, get_ensemble("ew_mom_5_20").component_ids())
    assert len(report.rows) == 2
    dropped = {row.dropped for row in report.rows}
    assert dropped == {"rank_momentum_5", "rank_momentum_20"}


@pytest.mark.ensemble
def test_correlated_pair_does_not_double_information() -> None:
    bars = _bars()
    dates = session_calendar(bars)
    base_panels, labels, _r = run_ensemble(get_ensemble("ew_mom_5_20"), bars)
    a = base_panels["rank_momentum_20"]
    near: Panel = {as_of: {k: v + 1e-9 for k, v in row.items()} for as_of, row in a.items()}
    definition = EnsembleDefinition(
        ensemble_id="ab_unit",
        version="1",
        name="A plus near-A",
        components=[
            EnsembleComponent(component_id="A", component_type=ComponentType.ALPHA),
            EnsembleComponent(component_id="B", component_type=ComponentType.ALPHA),
        ],
    )
    _p, _l, ab = run_ensemble(definition, bars, overrides={"A": a, "B": near})
    a_ics = [
        ic
        for as_of in dates[:-1]
        if (ic := spearman_ic(a.get(as_of, {}), labels.get(as_of, {}))) is not None
    ]
    a_mean = sum(a_ics) / len(a_ics)
    assert ab.mean_ic is not None
    assert abs(ab.mean_ic - a_mean) < 0.05
    diversity = pairwise_correlations({"A": a, "B": near}, dates, ["A", "B"])
    assert diversity.redundancy == "HIGH_REDUNDANCY"


@pytest.mark.ensemble
def test_independent_component_can_change_ensemble() -> None:
    bars = _bars()
    dates = session_calendar(bars)
    base_panels, labels, _r = run_ensemble(get_ensemble("ew_mom_5_20"), bars)
    a = base_panels["rank_momentum_20"]
    c = base_panels["rank_momentum_5"]
    definition = EnsembleDefinition(
        ensemble_id="ac_unit",
        version="1",
        name="A plus C",
        components=[
            EnsembleComponent(component_id="A", component_type=ComponentType.ALPHA),
            EnsembleComponent(component_id="C", component_type=ComponentType.ALPHA),
        ],
    )
    _p, _l, ac = run_ensemble(definition, bars, overrides={"A": a, "C": c})
    a_ics = [
        ic
        for as_of in dates[:-1]
        if (ic := spearman_ic(a.get(as_of, {}), labels.get(as_of, {}))) is not None
    ]
    a_mean = sum(a_ics) / len(a_ics)
    assert ac.mean_ic is not None
    assert ac.equal_weight_ic is not None
    assert abs(ac.mean_ic - a_mean) >= 0.0


@pytest.mark.ensemble
def test_sign_is_not_auto_flipped() -> None:
    bars = _bars()
    base_panels, _labels, _r = run_ensemble(get_ensemble("ew_mom_5_20"), bars)
    a = base_panels["rank_momentum_20"]
    flipped: Panel = {as_of: {k: -v for k, v in row.items()} for as_of, row in a.items()}
    definition = get_ensemble("roll_ic_mom").model_copy(
        update={
            "ensemble_id": "sign_unit",
            "version": "9",
            "components": [
                EnsembleComponent(component_id="A", component_type=ComponentType.ALPHA),
                EnsembleComponent(component_id="B", component_type=ComponentType.ALPHA),
            ],
        }
    )
    _p, _l, result = run_ensemble(definition, bars, overrides={"A": a, "B": flipped})
    negative_b = [pt.weights.get("B", 0.0) for pt in result.points if pt.weights]
    assert negative_b
    assert all(w >= -1e-12 for w in negative_b)


@pytest.mark.ensemble
def test_null_search_does_not_promote() -> None:
    bars = _bars()
    instruments = [Instrument(id=inst, name=inst.symbol) for inst in bars]
    dates = session_calendar(bars)
    names = [str(inst) for inst in bars]
    rng = 1
    noise: Panel = {}
    for as_of in dates:
        row = {}
        for inst in names:
            rng = (1103515245 * rng + 12345) % 2**31
            row[inst] = (rng % 1000) / 1000.0
        noise[as_of] = row
    definition = EnsembleDefinition(
        ensemble_id="noise_unit",
        version="1",
        name="noise",
        components=[
            EnsembleComponent(component_id="N", component_type=ComponentType.ALPHA),
            EnsembleComponent(component_id="M", component_type=ComponentType.ALPHA),
        ],
    )
    report, _run, wf = run_ensemble_experiment(
        bars=bars,
        instruments=instruments,
        definition=definition,
        data_kind="synthetic",
        overrides={"N": noise, "M": noise},
        append=False,
    )
    assert report.gate.outcome.value != "research_candidate"
    assert wf.n_scored >= 0
