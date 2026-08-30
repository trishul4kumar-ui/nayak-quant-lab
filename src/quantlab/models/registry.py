from __future__ import annotations

import json
from pathlib import Path

from quantlab.domain.models import ExperimentRun


class ExperimentLedger:
    """Append-only JSONL. Postgres later; this is the contract."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, run: ExperimentRun) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(run.model_dump_json() + "\n")

    def list_runs(self) -> list[ExperimentRun]:
        if not self.path.exists():
            return []
        runs: list[ExperimentRun] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                runs.append(ExperimentRun.model_validate(json.loads(line)))
        return runs

    def get(self, experiment_id: str) -> ExperimentRun | None:
        runs = self.list_runs()
        exact = [run for run in runs if run.id == experiment_id]
        if exact:
            return exact[-1]
        prefix = [run for run in runs if run.id.startswith(experiment_id)]
        if not prefix:
            return None
        return prefix[-1]
