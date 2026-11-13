from __future__ import annotations

from datetime import UTC, datetime

import pytest

from quantlab.agent_desk.desktop_actions import (
    _DENIED_INTENT,
    ChartAction,
    DesktopPlan,
    DesktopStep,
    MarketBacktestAction,
    PlanScope,
    ShowResultsAction,
    SyntheticBacktestAction,
    affirmative_task,
    planner_schema,
    task_constraints,
    validate_plan,
)
from quantlab.agents.errors import AgentContextError
from quantlab.agents.hashing import digest


def scope(task: str = "ANY", requested: tuple[str, ...] = ()) -> PlanScope:
    return PlanScope.model_validate(
        {
            "created_at": datetime.now(UTC),
            "request_id": "real-test",
            "configured_instruments": ["BSE:BEL", "NSE:INFY"],
            "requested_task": task,
            "requested_instruments": requested,
        }
    )


def plan(context: PlanScope, action) -> DesktopPlan:
    return DesktopPlan(
        created_at=datetime.now(UTC),
        request_id=context.request_id,
        scope_hash=context.content_hash,
        objective="Research",
        steps=(DesktopStep(step_id="s1", role="QUANT", action=action),),
    )


def test_real_backtest_allowed_only_with_real_typed_action() -> None:
    context = scope("REAL_BACKTEST", ("BSE:BEL",))
    validate_plan(plan(context, MarketBacktestAction(instrument="BSE:BEL")), context)
    with pytest.raises(AgentContextError, match="SYNTHETIC_SUBSTITUTION_DENIED"):
        validate_plan(plan(context, SyntheticBacktestAction()), context)
    with pytest.raises(AgentContextError, match="REQUESTED_REAL_BACKTEST_MISSING"):
        validate_plan(plan(context, ChartAction(instrument="BSE:BEL")), context)
    with pytest.raises(AgentContextError, match="REQUESTED_INSTRUMENT_MISMATCH"):
        validate_plan(plan(context, MarketBacktestAction(instrument="NSE:INFY")), context)
    wrong_results = DesktopPlan(
        created_at=datetime.now(UTC),
        request_id=context.request_id,
        scope_hash=context.content_hash,
        objective="Wrong existing result",
        steps=(
            DesktopStep(
                step_id="s1", role="QUANT", action=MarketBacktestAction(instrument="BSE:BEL")
            ),
            DesktopStep(
                step_id="s2",
                role="QUANT",
                action=ShowResultsAction(source="existing", experiment_id="older-run"),
            ),
        ),
    )
    with pytest.raises(AgentContextError, match="REQUESTED_OWNED_RESULT_REQUIRED"):
        validate_plan(wrong_results, context)


def test_chart_only_scope_cannot_be_replaced_by_any_backtest() -> None:
    context = scope("CHART_ONLY", ("BSE:BEL",))
    validate_plan(plan(context, ChartAction(instrument="BSE:BEL")), context)
    for action in (SyntheticBacktestAction(), MarketBacktestAction(instrument="BSE:BEL")):
        with pytest.raises(AgentContextError):
            validate_plan(plan(context, action), context)


@pytest.mark.parametrize(
    "task,forbidden",
    [
        ("REAL_BACKTEST", {"SyntheticBacktestAction", "SyntheticValidationAction"}),
        (
            "CHART_ONLY",
            {"SyntheticBacktestAction", "SyntheticValidationAction", "MarketBacktestAction"},
        ),
        ("SYNTHETIC_RESEARCH", {"MarketBacktestAction"}),
    ],
)
def test_transport_grammar_restricts_task_not_just_final_validation(task, forbidden) -> None:
    schema = planner_schema(scope(task, ("BSE:BEL",)))
    branches = schema["$defs"]["DesktopStep"]["properties"]["action"]["oneOf"]
    assert not forbidden.intersection(branch["$ref"].split("/")[-1] for branch in branches)
    assert schema["$defs"]["MarketBacktestAction"]["properties"]["instrument"]["enum"] == [
        "BSE:BEL"
    ]


def test_intent_binding_and_negated_order_wording() -> None:
    question = "Backtest BSE:BEL using real live data. Do not place orders or run synthetic tests."
    assert task_constraints(question, ("BSE:BEL", "NSE:INFY")) == {
        "requested_task": "REAL_BACKTEST",
        "requested_instruments": ("BSE:BEL",),
    }
    assert _DENIED_INTENT.search(affirmative_task(question)) is None
    assert _DENIED_INTENT.search(affirmative_task("Do not place orders, but submit trades"))
    assert _DENIED_INTENT.search(affirmative_task("Do not place orders. Instead execute trades"))
    assert (
        task_constraints("Open the BSE:BEL chart. Do not run synthetic backtests.", ("BSE:BEL",))[
            "requested_task"
        ]
        == "CHART_ONLY"
    )
    assert (
        task_constraints("Run a test on BSE:BEL stock", ("BSE:BEL",))["requested_task"]
        == "REAL_BACKTEST"
    )
    assert (
        task_constraints("Backtest BSE:BEL with real data, no synthetic data.", ("BSE:BEL",))[
            "requested_task"
        ]
        == "REAL_BACKTEST"
    )


def test_old_unconstrained_scope_hash_survives_reload() -> None:
    context = scope()
    original = context.model_dump(mode="json", exclude={"content_hash"})
    assert "requested_task" not in original
    assert context.content_hash == digest({"contract": "PlanScope", "payload": original})
    assert (
        PlanScope.model_validate({**original, "content_hash": context.content_hash}).content_hash
        == context.content_hash
    )
