"""Replication: same spec + same snapshot = same identity. New snapshot = new lineage."""

from __future__ import annotations

from pydantic import BaseModel

from quantlab.orchestration.errors import OrchestrationError
from quantlab.orchestration.snapshot import DatasetSnapshot
from quantlab.orchestration.specification import ResearchSpec


class ReplicationReport(BaseModel):
    parent_experiment: str
    replica_experiment: str
    same_identity: bool
    same_snapshot: bool
    same_result: bool | None
    note: str = "Cross-sectional replication on synthetic data remains NOT_TESTED."


def replication_identity(
    parent: ResearchSpec,
    replica: ResearchSpec,
    parent_snapshot: DatasetSnapshot,
    replica_snapshot: DatasetSnapshot,
) -> ReplicationReport:
    same_id = parent.identity_hash() == replica.identity_hash()
    same_snap = parent_snapshot.identity_hash() == replica_snapshot.identity_hash()
    if same_id and not same_snap:
        raise OrchestrationError(
            "replication contamination: same experiment identity on a different snapshot"
        )
    return ReplicationReport(
        parent_experiment=parent.experiment_id,
        replica_experiment=replica.experiment_id,
        same_identity=same_id,
        same_snapshot=same_snap,
        same_result=None,
        note=(
            "same spec + same snapshot must match; a new snapshot is a new lineage. "
            "Cross-market replication is NOT_TESTED on synthetic bars."
        ),
    )
