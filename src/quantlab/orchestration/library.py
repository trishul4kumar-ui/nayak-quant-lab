"""Seed hypotheses, families, and search spaces. Seeds are not engine-hardcoded logic."""

from __future__ import annotations

from quantlab.orchestration.contracts import (
    ExperimentType,
    MetricRole,
    ResearchStatus,
    SelectionPolicy,
    StoppingPolicy,
)
from quantlab.orchestration.family import ResearchFamily
from quantlab.orchestration.hypothesis import HypothesisSpec
from quantlab.orchestration.search_space import SearchDimension, SearchSpace
from quantlab.orchestration.specification import MetricSpec, ResearchSpec


def seed_hypotheses() -> list[HypothesisSpec]:
    return [
        HypothesisSpec(
            hypothesis_id="H-MOM-001",
            version="1",
            title="Cross-sectional momentum persists one session",
            description=(
                "Names with higher 20-session momentum outperform on the next bar after costs."
            ),
            economic_rationale="Underreaction / trend following in a small synthetic universe.",
            null_hypothesis="Next-bar returns are independent of momentum rank.",
            expected_direction="long_high",
            target="next_bar_return",
            horizon="1d",
            status=ResearchStatus.REGISTERED,
            tags=["momentum", "cross_section", "synthetic"],
            provenance="prompt14-seed",
            notes=(
                "H-MOM-001 is a documentation seed, not a claim of NSE alpha. "
                "Synthetic drift validates orchestration, not markets."
            ),
        )
    ]


def seed_search_spaces() -> list[SearchSpace]:
    return [
        SearchSpace(
            search_space_id="mom_lookback_cost",
            version="1",
            dimensions=[
                SearchDimension(name="lookback", values=[5, 20]),
                SearchDimension(name="cost_bps", values=[10.0, 20.0]),
                SearchDimension(name="top_n", values=[2]),
            ],
            notes="Small pre-registered grid. Every cell is recorded, including losers.",
        )
    ]


def seed_families() -> list[ResearchFamily]:
    return [
        ResearchFamily(
            family_id="MOM-FAMILY-001",
            version="1",
            hypothesis_id="H-MOM-001",
            search_space_id="mom_lookback_cost",
            baseline_id="equal_weight",
            selection_policy=SelectionPolicy.PRE_REGISTERED,
            stopping_policy=StoppingPolicy.PRE_REGISTERED_BUDGET,
            multiple_testing_method="benjamini_hochberg",
        )
    ]


def seed_specs() -> list[ResearchSpec]:
    return [
        ResearchSpec(
            experiment_id="EXP-MOM-001",
            experiment_version="1",
            hypothesis_id="H-MOM-001",
            family_id="MOM-FAMILY-001",
            experiment_type=ExperimentType.DISCOVERY,
            multiple_testing_family="MOM-FAMILY-001",
            lookback=20,
            top_n=2,
            cost_bps=10.0,
            metrics=[
                MetricSpec(name="total_return", role=MetricRole.PRIMARY),
                MetricSpec(name="sharpe", role=MetricRole.SECONDARY),
                MetricSpec(name="max_drawdown", role=MetricRole.DIAGNOSTIC),
            ],
        )
    ]
