from collections.abc import Iterator
from pathlib import Path

import pytest

from quantlab.core.config import get_settings


@pytest.fixture(autouse=True)
def isolate_default_test_storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Default repository/desktop stores must never touch the user's research files."""
    monkeypatch.setenv("EXPERIMENT_LEDGER_PATH", str(tmp_path / "experiments" / "ledger.jsonl"))
    monkeypatch.setenv("QUANT_LAB_DATA_DIR", str(tmp_path / "desktop"))
    get_settings.cache_clear()
    try:
        yield
    finally:
        get_settings.cache_clear()


@pytest.fixture
def tmp_ledger(tmp_path: Path) -> Path:
    return tmp_path / "ledger.jsonl"
