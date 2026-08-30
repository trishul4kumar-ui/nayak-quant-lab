from __future__ import annotations

import pytest

from quantlab.knowledge.entities import NodeType, RelationType

pytestmark = pytest.mark.knowledge


def test_required_node_types_exist() -> None:
    required = {
        "HYPOTHESIS",
        "EXPRESSION",
        "FEATURE",
        "FACTOR",
        "ALPHA",
        "MODEL",
        "ADAPTIVE_LEARNER",
        "ENSEMBLE",
        "REGIME",
        "PORTFOLIO",
        "EXPERIMENT",
        "DISCOVERY_RUN",
        "EVIDENCE",
        "FALSIFICATION",
        "REPLICATION",
        "VALIDATION",
        "DATASET_SNAPSHOT",
        "EXECUTION_ASSUMPTION",
        "RESEARCH_RESULT",
        "RESEARCH_CLAIM",
    }
    assert required <= {item.name for item in NodeType}


def test_genealogy_relations_exist() -> None:
    for name in (
        "DERIVED_FROM",
        "MUTATED_FROM",
        "CROSSED_FROM",
        "FALSIFIED_BY",
        "SUPERSEDES",
        "CONTRADICTS",
        "SUPPORTS",
    ):
        assert hasattr(RelationType, name)
