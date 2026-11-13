"""Append-only in-process registries. Completed identities are never overwritten."""

from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel

from quantlab.backtest.spec import config_hash
from quantlab.orchestration.contracts import ResearchStatus
from quantlab.orchestration.errors import OrchestrationError
from quantlab.orchestration.family import ResearchFamily
from quantlab.orchestration.hypothesis import HypothesisSpec
from quantlab.orchestration.library import (
    seed_families,
    seed_hypotheses,
    seed_search_spaces,
    seed_specs,
)
from quantlab.orchestration.search_space import SearchSpace
from quantlab.orchestration.specification import ResearchPlan, ResearchSpec
from quantlab.orchestration.status import transition

_Model = TypeVar("_Model", bound=BaseModel)
_Key = str | tuple[str, str]


class OrchestrationRegistry:
    def __init__(self) -> None:
        self._hypotheses: dict[tuple[str, str], HypothesisSpec] = {}
        self._spaces: dict[str, SearchSpace] = {}
        self._families: dict[str, ResearchFamily] = {}
        self._specs: dict[tuple[str, str], ResearchSpec] = {}
        self._plans: dict[str, ResearchPlan] = {}
        self._finalized: set[tuple[str, str]] = set()
        self._hashes: dict[tuple[str, _Key], str] = {}
        for hypothesis in seed_hypotheses():
            self.register_hypothesis(hypothesis)
        for space in seed_search_spaces():
            self.register_search_space(space)
        for family in seed_families():
            self.register_family(family)
        for spec in seed_specs():
            self.register_spec(spec)

    def _snapshot(self, namespace: str, key: _Key, value: _Model) -> _Model:
        snapshot = value.model_copy(deep=True)
        self._hashes[(namespace, key)] = config_hash(snapshot.model_dump(mode="json"))
        return snapshot

    def _verified_copy(self, namespace: str, key: _Key, value: _Model) -> _Model:
        expected = self._hashes.get((namespace, key))
        if expected is None or expected != config_hash(value.model_dump(mode="json")):
            raise OrchestrationError(f"registered {namespace} integrity mismatch: {key}")
        return value.model_copy(deep=True)

    def register_hypothesis(self, spec: HypothesisSpec) -> None:
        key = (spec.hypothesis_id, spec.version)
        if key in self._hypotheses:
            raise OrchestrationError(
                f"cannot overwrite hypothesis {spec.hypothesis_id}@{spec.version}"
            )
        self._hypotheses[key] = self._snapshot("hypothesis", key, spec)

    def register_search_space(self, space: SearchSpace) -> None:
        if space.search_space_id in self._spaces:
            raise OrchestrationError(f"cannot overwrite search space {space.search_space_id}")
        self._spaces[space.search_space_id] = self._snapshot(
            "search_space", space.search_space_id, space
        )

    def register_family(self, family: ResearchFamily) -> None:
        if family.family_id in self._families:
            raise OrchestrationError(f"cannot overwrite family {family.family_id}")
        self._families[family.family_id] = self._snapshot("family", family.family_id, family)

    def register_spec(self, spec: ResearchSpec) -> None:
        key = (spec.experiment_id, spec.experiment_version)
        if key in self._specs:
            raise OrchestrationError(
                f"cannot overwrite experiment {spec.experiment_id}@{spec.experiment_version}"
            )
        self._specs[key] = self._snapshot("spec", key, spec)

    def finalize(self, experiment_id: str, version: str) -> None:
        key = (experiment_id, version)
        if key not in self._specs:
            raise OrchestrationError(f"unknown experiment {experiment_id}@{version}")
        self._verified_copy("spec", key, self._specs[key])
        self._finalized.add(key)

    def assert_not_finalized(self, experiment_id: str, version: str) -> None:
        if (experiment_id, version) in self._finalized:
            raise OrchestrationError(
                f"result overwrite of finalized experiment {experiment_id}@{version}"
            )

    def put_plan(self, plan: ResearchPlan) -> None:
        existing = self._plans.get(plan.plan_id)
        if existing is not None:
            verified = self._verified_copy("plan", plan.plan_id, existing)
            if verified.identity_hash() != plan.identity_hash():
                raise OrchestrationError(f"cannot overwrite plan {plan.plan_id}; bump version")
            return
        self._plans[plan.plan_id] = self._snapshot("plan", plan.plan_id, plan)

    def get_hypothesis(self, hypothesis_id: str, version: str | None = None) -> HypothesisSpec:
        if version is not None:
            found = self._hypotheses.get((hypothesis_id, version))
            if found is None:
                raise OrchestrationError(f"unknown hypothesis {hypothesis_id}@{version}")
            return self._verified_copy("hypothesis", (hypothesis_id, version), found)
        keys = [key for key in self._hypotheses if key[0] == hypothesis_id]
        if not keys:
            raise OrchestrationError(f"unknown hypothesis {hypothesis_id}")
        key = keys[-1]
        return self._verified_copy("hypothesis", key, self._hypotheses[key])

    def get_family(self, family_id: str) -> ResearchFamily:
        if family_id not in self._families:
            raise OrchestrationError(f"unknown family {family_id}")
        return self._verified_copy("family", family_id, self._families[family_id])

    def get_search_space(self, search_space_id: str) -> SearchSpace:
        if search_space_id not in self._spaces:
            raise OrchestrationError(f"unknown search space {search_space_id}")
        return self._verified_copy("search_space", search_space_id, self._spaces[search_space_id])

    def get_spec(self, experiment_id: str, version: str | None = None) -> ResearchSpec:
        if version is not None:
            found = self._specs.get((experiment_id, version))
            if found is None:
                raise OrchestrationError(f"unknown experiment {experiment_id}@{version}")
            return self._verified_copy("spec", (experiment_id, version), found)
        keys = [key for key in self._specs if key[0] == experiment_id]
        if not keys:
            raise OrchestrationError(f"unknown experiment {experiment_id}")
        key = keys[-1]
        return self._verified_copy("spec", key, self._specs[key])

    def get_plan(self, plan_id: str) -> ResearchPlan:
        if plan_id not in self._plans:
            raise OrchestrationError(f"unknown plan {plan_id}")
        return self._verified_copy("plan", plan_id, self._plans[plan_id])

    def list_hypotheses(self) -> list[HypothesisSpec]:
        return [self._verified_copy("hypothesis", key, value)
                for key, value in self._hypotheses.items()]

    def list_families(self) -> list[ResearchFamily]:
        return [self._verified_copy("family", key, value)
                for key, value in self._families.items()]

    def list_specs(self) -> list[ResearchSpec]:
        return [self._verified_copy("spec", key, value) for key, value in self._specs.items()]

    def list_search_spaces(self) -> list[SearchSpace]:
        return [self._verified_copy("search_space", key, value)
                for key, value in self._spaces.items()]

    def set_hypothesis_status(
        self, hypothesis_id: str, status: ResearchStatus, *, version: str | None = None
    ) -> HypothesisSpec:
        current = self.get_hypothesis(hypothesis_id, version)
        transition(current.status, status)
        updated = current.model_copy(update={"status": status})
        key = (updated.hypothesis_id, updated.version)
        self._hypotheses[key] = self._snapshot("hypothesis", key, updated)
        return updated.model_copy(deep=True)


_DEFAULT = OrchestrationRegistry()


def default_registry() -> OrchestrationRegistry:
    return _DEFAULT


def get_hypothesis(hypothesis_id: str, version: str | None = None) -> HypothesisSpec:
    return _DEFAULT.get_hypothesis(hypothesis_id, version)


def get_family(family_id: str) -> ResearchFamily:
    return _DEFAULT.get_family(family_id)


def get_search_space(search_space_id: str) -> SearchSpace:
    return _DEFAULT.get_search_space(search_space_id)


def get_spec(experiment_id: str, version: str | None = None) -> ResearchSpec:
    return _DEFAULT.get_spec(experiment_id, version)


def list_hypotheses() -> list[HypothesisSpec]:
    return _DEFAULT.list_hypotheses()


def list_families() -> list[ResearchFamily]:
    return _DEFAULT.list_families()


def list_specs() -> list[ResearchSpec]:
    return _DEFAULT.list_specs()
