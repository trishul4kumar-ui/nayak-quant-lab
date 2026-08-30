"""Discovery report. Discovery survivor ≠ research candidate."""

from __future__ import annotations

from pydantic import BaseModel, Field

from quantlab.discovery.lineage import DiscoveryLineage
from quantlab.discovery.population import DiscoveryCandidate
from quantlab.domain.research import CheckResult
from quantlab.research.gate import ResearchGateResult
from quantlab.research.multiple_testing import MultipleTestingReport


class DiscoveryReport(BaseModel):
    schema_version: str = "1"
    family_id: str
    discovery_run_id: str
    grammar_version: str
    snapshot_id: str
    data_kind: str = "synthetic"
    tested_count: int = 0
    hidden: bool = False
    elite_text: str = ""
    elite_hash: str = ""
    train_ic: float | None = None
    validation_ic: float | None = None
    holdout_ic: float | None = None
    novelty: str = ""
    complexity: float = 0.0
    candidates: list[DiscoveryCandidate] = Field(default_factory=list)
    lineage: DiscoveryLineage | None = None
    multiple_testing: MultipleTestingReport | None = None
    gate: ResearchGateResult | None = None
    discovery_status: str = "explored"
    integrity_status: str = CheckResult.NOT_TESTED.value
    validation_status: str = CheckResult.NOT_TESTED.value
    replication_status: str = CheckResult.NOT_TESTED.value
    pit_integrity: dict[str, str] = Field(default_factory=dict)
    not_tested: list[str] = Field(default_factory=list)
    conclusion: str = ""
    config_hash: str = ""
    live_trading: bool = False
