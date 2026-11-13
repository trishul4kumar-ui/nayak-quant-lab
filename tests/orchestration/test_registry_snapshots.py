import pytest

from quantlab.orchestration.contracts import ResearchStatus
from quantlab.orchestration.errors import OrchestrationError
from quantlab.orchestration.family import ResearchFamily
from quantlab.orchestration.hypothesis import HypothesisSpec
from quantlab.orchestration.registry import OrchestrationRegistry
from quantlab.orchestration.search_space import SearchDimension, SearchSpace
from quantlab.orchestration.specification import ResearchPlan, ResearchSpec


def test_registered_family_and_search_grid_are_defensive_snapshots() -> None:
    store = OrchestrationRegistry()
    family = ResearchFamily(family_id="test-family", hypothesis_id="hyp", search_space_id="space")
    space = SearchSpace(
        search_space_id="test-space", dimensions=[SearchDimension(name="lookback", values=[2, 4])]
    )
    store.register_family(family)
    store.register_search_space(space)
    family.hypothesis_id = "changed"
    space.dimensions[0].values.append(8)
    assert store.get_family("test-family").hypothesis_id == "hyp"
    assert store.get_search_space("test-space").dimensions[0].values == [2, 4]

    read = store.get_search_space("test-space")
    read.dimensions[0].values.clear()
    listed = next(item for item in store.list_families() if item.family_id == "test-family")
    listed.hypothesis_id = "also-changed"
    assert store.get_search_space("test-space").dimensions[0].values == [2, 4]
    assert store.get_family("test-family").hypothesis_id == "hyp"


def test_plan_snapshot_cannot_be_mutated_or_replaced_by_collision() -> None:
    store = OrchestrationRegistry()
    spec = ResearchSpec(experiment_id="test-spec", hypothesis_id="hyp", family_id="family")
    plan = ResearchPlan(plan_id="test-plan", spec=spec)
    store.register_spec(spec)
    store.put_plan(plan)
    spec.universe.append("NSE:EXAMPLE")
    plan.spec.metrics[0].name = "changed"
    assert store.get_spec("test-spec").universe == []
    assert store.get_plan("test-plan").spec.metrics[0].name == "total_return"
    returned = store.get_plan("test-plan")
    returned.spec.metrics[0].name = "changed-again"
    assert store.get_plan("test-plan").spec.metrics[0].name == "total_return"
    with pytest.raises(OrchestrationError, match="cannot overwrite plan"):
        store.put_plan(returned)


def test_private_tampering_fails_closed_on_read_and_list() -> None:
    store = OrchestrationRegistry()
    family = ResearchFamily(family_id="test-family", hypothesis_id="hyp", search_space_id="space")
    store.register_family(family)
    store._families["test-family"].notes = "tampered"
    with pytest.raises(OrchestrationError, match="integrity mismatch"):
        store.get_family("test-family")
    with pytest.raises(OrchestrationError, match="integrity mismatch"):
        store.list_families()


def test_hypothesis_status_update_is_explicit_and_defensive() -> None:
    store = OrchestrationRegistry()
    hypothesis = HypothesisSpec(hypothesis_id="test-hyp", title="title", description="description")
    store.register_hypothesis(hypothesis)
    hypothesis.tags.append("not-registered")
    assert store.get_hypothesis("test-hyp").tags == []
    updated = store.set_hypothesis_status("test-hyp", ResearchStatus.PLANNED)
    updated.tags.append("not-registered")
    assert store.get_hypothesis("test-hyp").tags == []
    assert store.get_hypothesis("test-hyp").status is ResearchStatus.PLANNED
