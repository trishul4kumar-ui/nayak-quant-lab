"""On-disk fabric layers. Raw is immutable."""

from __future__ import annotations

import os
from pathlib import Path


class FabricLayout:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.raw = root / "raw"
        self.normalized = root / "normalized"
        self.curated = root / "curated"
        self.pit = root / "pit"
        self.features = root / "features"
        self.metadata = root / "metadata"
        self.quarantine = root / "quarantine"

    def ensure(self) -> None:
        for folder in (
            self.raw,
            self.normalized,
            self.curated,
            self.pit,
            self.features,
            self.metadata,
            self.quarantine,
        ):
            folder.mkdir(parents=True, exist_ok=True)

    def catalog_path(self) -> Path:
        return self.metadata / "catalog.sqlite"

    def duckdb_path(self) -> Path:
        return self.metadata / "fabric.duckdb"

    def raw_dir(self, dataset_id: str, version: str) -> Path:
        path = self.raw / dataset_id / version
        path.mkdir(parents=True, exist_ok=True)
        return path

    def pit_dir(self, dataset_id: str, version: str) -> Path:
        path = self.pit / dataset_id / version
        path.mkdir(parents=True, exist_ok=True)
        return path

    def quarantine_dir(self, dataset_id: str, version: str) -> Path:
        path = self.quarantine / dataset_id / version
        path.mkdir(parents=True, exist_ok=True)
        return path

    def normalized_dir(self, dataset_id: str, version: str) -> Path:
        path = self.normalized / dataset_id / version
        path.mkdir(parents=True, exist_ok=True)
        return path

    def curated_dir(self, dataset_id: str, version: str) -> Path:
        path = self.curated / dataset_id / version
        path.mkdir(parents=True, exist_ok=True)
        return path


def resolve_fabric_root(override: Path | None = None) -> Path:
    """CLI/default fabric root. Desktop uses RuntimePaths.fabric_dir instead."""
    if override is not None:
        return override
    env = os.environ.get("QUANT_LAB_DATA_DIR")
    if env:
        return Path(env) / "fabric"
    return Path("data")
