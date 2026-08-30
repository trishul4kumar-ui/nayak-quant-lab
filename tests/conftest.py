from pathlib import Path

import pytest


@pytest.fixture
def tmp_ledger(tmp_path: Path) -> Path:
    return tmp_path / "ledger.jsonl"
