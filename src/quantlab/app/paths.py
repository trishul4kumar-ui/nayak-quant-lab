"""OS-appropriate application data. No hardcoded /Users or C:\\ paths."""

from __future__ import annotations

import os
import sys
from pathlib import Path


class RuntimePaths:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.logs_dir = root / "logs"
        self.research_dir = root / "research"
        self.artifacts_dir = root / "artifacts"
        self.database_dir = root / "database"
        self.settings_dir = root / "settings"
        self.db_path = self.database_dir / "app.sqlite"
        self.settings_path = self.settings_dir / "ui.json"
        self.ledger_path = self.research_dir / "ledger.jsonl"
        self.log_file = self.logs_dir / "quantlab.log"
        self.fabric_dir = root / "fabric"

    def ensure(self) -> None:
        for folder in (
            self.logs_dir,
            self.research_dir,
            self.artifacts_dir,
            self.database_dir,
            self.settings_dir,
            self.fabric_dir,
        ):
            folder.mkdir(parents=True, exist_ok=True)

    @classmethod
    def discover(cls, override: Path | None = None) -> RuntimePaths:
        if override is not None:
            return cls(override)
        env = os.environ.get("QUANT_LAB_DATA_DIR")
        if env:
            return cls(Path(env))
        if sys.platform == "darwin":
            root = Path.home() / "Library" / "Application Support" / "QUANT LAB"
        elif sys.platform == "win32":
            roaming = os.environ.get("APPDATA")
            base = Path(roaming) if roaming else Path.home() / "AppData" / "Roaming"
            root = base / "QUANT LAB"
        else:
            root = Path.home() / ".local" / "share" / "quantlab"
        return cls(root)
