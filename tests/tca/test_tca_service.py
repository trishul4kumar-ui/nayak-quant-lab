from __future__ import annotations

from datetime import UTC, datetime

import pytest

from quantlab import __version__
from quantlab.core.errors import SafetyError
from quantlab.domain.models import Side
from quantlab.domain.research import CheckResult
from quantlab.paper_oms.library import seed_account, seed_decision, seed_snapshot, seed_target
from quantlab.paper_oms.models import PaperFill, PaperOMSRequest
from quantlab.paper_oms.service import run_paper_oms
from quantlab.tca.calibration import calibrate_impact
from quantlab.tca.capacity import LADDER, capacity_from_liquidity
from quantlab.tca.enums import ArrivalPolicy, TCAKind
from quantlab.tca.errors import CalibrationError, TCAError
from quantlab.tca.models import CapacityPolicy, LiquidityObservation, TCARequest
from quantlab.tca.service import run_tca
from quantlab.tca.shortfall import shortfall_from_fills, signed_slippage
from quantlab.tca.state import reset as reset_tca


def _paper():
    return run_paper_oms(
        PaperOMSRequest(),
        decision=seed_decision(),
        target=seed_target(),
        account=seed_account(),
        snapshot=seed_snapshot(),
    )


def _fill(*, side: Side, arrival: float, execution: float, qty: float = 10.0) -> PaperFill:
    return PaperFill(
        fill_id="F1",
        order_id="O1",
        security_id="NSE:AAA",
        side=side,
        requested_quantity=qty,
        filled_quantity=qty,
        remaining_quantity=0.0,
        reference_price=arrival,
        arrival_price=arrival,
        execution_price=execution,
        gross_notional=qty * execution,
        arrival_time=datetime(2024, 1, 15, tzinfo=UTC),
        fill_time=datetime(2024, 1, 15, tzinfo=UTC),
        execution_model_id="base",
        spread_cost=0.1,
        slippage_cost=abs(execution - arrival) * qty,
        impact_cost=0.0,
        commission=0.0,
        taxes=0.0,
        fees=0.0,
        total_cost=0.1,
    )


def test_version() -> None:
    assert __version__ == "3.1.0"


@pytest.mark.parametrize("side", [Side.BUY, Side.SELL])
def test_slippage_sign(side: Side) -> None:
    arrival = 100.0
    execution = 101.0 if side is Side.BUY else 99.0
    fill = _fill(side=side, arrival=arrival, execution=execution)
    slip = signed_slippage(fill, arrival)
    assert slip >= 0.0


def test_wrong_side_buy_fails() -> None:
    fill = _fill(side=Side.BUY, arrival=100.0, execution=99.0)
    with pytest.raises(TCAError, match="wrong_side"):
        shortfall_from_fills([fill], policy=ArrivalPolicy.ARRIVAL_SNAPSHOT)


def test_wrong_side_sell_fails() -> None:
    fill = _fill(side=Side.SELL, arrival=100.0, execution=101.0)
    with pytest.raises(TCAError, match="wrong_side"):
        shortfall_from_fills([fill], policy=ArrivalPolicy.ARRIVAL_SNAPSHOT)


def test_shortfall_decomposes() -> None:
    fill = _fill(side=Side.BUY, arrival=100.0, execution=101.0)
    item = shortfall_from_fills([fill], policy=ArrivalPolicy.ARRIVAL_SNAPSHOT)
    assert item.trading_cost is not None
    assert item.spread_cost is not None
    assert item.explicit_fees is not None
    assert item.total is not None
    assert item.status is CheckResult.PASS


def test_observed_vs_modelled_notes() -> None:
    paper = _paper()
    obs = run_tca(TCARequest(kind=TCAKind.OBSERVED), paper=paper)
    reset_tca()
    modelled = run_tca(TCARequest(kind=TCAKind.MODELLED), paper=paper)
    assert "observed" in obs.kind.value
    assert "modelled" in modelled.kind.value
    assert "MODELLED" in modelled.note or "modelled" in modelled.note.lower()


def test_calibration_window_leak() -> None:
    paper = _paper()
    with pytest.raises(CalibrationError):
        calibrate_impact(
            paper.fills,
            as_of=datetime(2024, 1, 1, tzinfo=UTC),
            window_end=datetime(2024, 6, 1, tzinfo=UTC),
            snapshot_id="seed",
        )


def test_calibration_freeze() -> None:
    paper = _paper()
    rec = calibrate_impact(
        paper.fills,
        as_of=datetime(2024, 1, 15, tzinfo=UTC),
        window_end=datetime(2024, 1, 15, tzinfo=UTC),
        snapshot_id="seed",
    )
    assert rec.frozen is True
    assert rec.parameter_hash


def test_missing_volume_capacity_not_tested() -> None:
    from quantlab.tca.enums import CapacityStatus

    result = capacity_from_liquidity(
        LiquidityObservation(volume=None),
        CapacityPolicy(policy_id="p", max_participation=0.1, max_cost_bps=50, min_net_edge=0),
        turnover=0.2,
        expected_edge=None,
        impact_k=None,
    )
    assert result.status is CapacityStatus.NOT_TESTED
    assert "NSE ADV" in result.note or "Not NSE" in result.note


def test_default_tca_never_promotes_seed_volume_to_liquidity() -> None:
    result = run_tca(paper=_paper())
    assert result.liquidity.volume is None
    assert result.liquidity.status is CheckResult.NOT_TESTED
    assert "typed liquidity" in result.liquidity.note.lower()


def test_typed_liquidity_evidence_is_explicit() -> None:
    result = run_tca(
        TCARequest(
            liquidity_observation=LiquidityObservation(
                volume=1_000_000.0,
                participation=0.05,
                status=CheckResult.PASS,
                note="Observed venue liquidity evidence, frozen for this test.",
            )
        ),
        paper=_paper(),
    )
    assert result.liquidity.volume == 1_000_000.0
    assert result.liquidity.status is CheckResult.PASS


@pytest.mark.parametrize("capital", list(LADDER))
def test_capacity_ladder_is_scenario(capital: float) -> None:
    assert capital in LADDER


def test_live_rejected() -> None:
    with pytest.raises(SafetyError):
        run_tca(TCARequest(live_trading=True), paper=_paper())


def test_future_payload_ignored() -> None:
    paper = _paper()
    a = run_tca(
        TCARequest(future_payload_ignored={"px": "999"}),
        paper=paper,
    )
    reset_tca()
    b = run_tca(paper=paper)
    assert a.run.tca_hash == b.run.tca_hash


def test_determinism_and_idempotency() -> None:
    paper = _paper()
    a = run_tca(paper=paper)
    b = run_tca(paper=paper)
    assert a.run.tca_run_id == b.run.tca_run_id
    reset_tca()
    c = run_tca(paper=paper)
    assert a.run.tca_hash == c.run.tca_hash


def test_paper_comparison_keys() -> None:
    result = run_tca(paper=_paper())
    assert "target_notional" in result.paper_comparison
    assert "tca_shortfall" in result.paper_comparison


def test_tax_legs_not_tested() -> None:
    result = run_tca(paper=_paper())
    names = {leg.name for leg in result.costs}
    assert "stt_bps" in names
    stt = next(leg for leg in result.costs if leg.name == "stt_bps")
    assert stt.status is CheckResult.NOT_TESTED


def test_knowledge_and_ledger(tmp_path) -> None:
    from quantlab.knowledge.ingest import persist_tca
    from quantlab.knowledge.serialization import load_graph
    from quantlab.tca.experiment import run_tca_experiment

    ledger = tmp_path / "ledger.jsonl"
    result, row = run_tca_experiment(ledger_path=ledger)
    persist_tca(result, ledger)
    graph = load_graph(ledger.with_name("knowledge.json"))
    types = {node.node_type.value for node in graph.nodes}
    assert "tca_run" in types
    assert row.tca_run_id == result.run.tca_run_id


def test_broker_absent() -> None:
    from pathlib import Path

    for path in Path("src/quantlab/tca").glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "kiteconnect" not in text
        assert "zerodha" not in text
        assert "openalgo" not in text
        assert "quantlab.brokers" not in text


@pytest.mark.parametrize(
    "flag",
    [
        "future_tca_observation",
        "calibration_window_leak",
        "arrival_price_lookahead",
        "synthetic_adv_claim",
        "observed_vs_modelled_confusion",
        "tca_parameter_mutation",
        "future_impact_calibration",
        "future_fill_observation",
    ],
)
def test_tca_integrity_flags(flag: str) -> None:
    from quantlab.research.integrity import evaluate_integrity

    report = evaluate_integrity(
        bars=[],
        states=[],
        as_of_times=[],
        next_bar_fill=True,
        cost_bps=10.0,
        slippage_model="configured",
        live_trading=False,
        n_experiments_in_family=1,
        used_ml=False,
        **{flag: True},
    )
    assert report.checks[flag] is CheckResult.FAIL


def test_cli_run(tmp_path) -> None:
    from quantlab.app.tca import list_payload, run_payload

    payload = run_payload(ledger=str(tmp_path / "ledger.jsonl"))
    assert payload["live_trading"] is False
    assert list_payload()
