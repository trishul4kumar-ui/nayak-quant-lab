"""Why QUANT LAB believes a claim: snapshot, protocol, hashes, software version."""

from __future__ import annotations

from pydantic import BaseModel, Field

from quantlab import __version__


class ProvenanceBundle(BaseModel):
    dataset_snapshot: str = ""
    snapshot_checksum: str = ""
    available_time_policy: str = "available_time <= decision_time"
    universe_definition: str = ""
    feature_identity: str = ""
    alpha_identity: str = ""
    model_identity: str = ""
    experiment_identity: str = ""
    search_space_id: str = ""
    selection_policy: str = ""
    backtest_configuration: str = "next_bar_cost_adjusted"
    cost_assumptions: str = "10bps"
    execution_assumptions: str = "research overlay; not broker fills"
    validation_protocol: str = "walk_forward_holdout_sacred"
    multiple_testing_family: str = "benjamini_hochberg"
    software_version: str = Field(default_factory=lambda: __version__)
    config_hash: str = ""

    def as_limitations(self, *, data_kind: str) -> list[str]:
        notes = [
            f"software={self.software_version}",
            f"policy={self.available_time_policy}",
        ]
        if data_kind == "synthetic":
            notes.extend(
                [
                    "synthetic data",
                    "no official holidays",
                    "no calibrated ADV",
                ]
            )
        return notes
