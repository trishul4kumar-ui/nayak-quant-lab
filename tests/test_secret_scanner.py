from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

SCANNER = Path(__file__).parents[1] / "scripts" / "check_tracked_secrets.py"


@pytest.mark.parametrize("quote", ["'", '"'])
def test_scanner_rejects_assignment_without_echoing_value(tmp_path: Path, quote: str) -> None:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    name = "_".join(("API", "KEY"))
    value = "scanner-fixture-not-a-credential"
    (tmp_path / "fixture.py").write_text(f"{name}={quote}{value}{quote}\n")
    subprocess.run(["git", "add", "fixture.py"], cwd=tmp_path, check=True)
    result = subprocess.run(
        [sys.executable, str(SCANNER)], cwd=tmp_path, capture_output=True, text=True, check=False
    )
    assert result.returncode == 1
    assert "fixture.py:1" in result.stdout
    assert value not in result.stdout


def test_scanner_accepts_clean_tracked_files(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "fixture.py").write_text("research_only=True\n")
    subprocess.run(["git", "add", "fixture.py"], cwd=tmp_path, check=True)
    result = subprocess.run(
        [sys.executable, str(SCANNER)], cwd=tmp_path, capture_output=True, text=True, check=False
    )
    assert result.returncode == 0
    assert "passed" in result.stdout
