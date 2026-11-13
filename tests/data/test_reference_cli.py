from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from quantlab.core.errors import DataIntegrityError
from quantlab.data.cli import add_data_parser, run_data_command
from tests.data.test_reference_data import document, raw


def _args(*items: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    add_data_parser(parser.add_subparsers(dest="command", required=True))
    return parser.parse_args(["data", *items])


def test_reference_import_and_as_of_query(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("QUANT_LAB_DATA_DIR", str(tmp_path / "runtime"))
    source = tmp_path / "source.json"
    source.write_bytes(raw(document()))
    assert run_data_command(_args("reference-ingest", str(source))) == 0
    imported = json.loads(capsys.readouterr().out)
    assert imported["status"] == "STORED_UNCERTIFIED"
    assert len(imported["source_checksum"]) == 64
    params = (
        "reference-query", "reference-demo", "v1", "NSE:TCS", "sector", "sector",
        "--allow-synthetic", "--as-of",
    )
    assert run_data_command(_args(*params, "2024-01-05T00:00:00Z")) == 0
    selected = json.loads(capsys.readouterr().out)
    assert selected["status"] == "OBSERVED_UNCERTIFIED"
    assert selected["observation"]["value"] == "technology"
    assert selected["data_kind"] == "synthetic"
    assert run_data_command(_args(*params, "2024-01-04T00:00:00Z")) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "NOT_FOUND"


def test_reference_query_refuses_naive_cutoff_and_synthetic_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("QUANT_LAB_DATA_DIR", str(tmp_path / "runtime"))
    source = tmp_path / "source.json"
    source.write_bytes(raw(document()))
    run_data_command(_args("reference-ingest", str(source)))
    capsys.readouterr()
    args = ("reference-query", "reference-demo", "v1", "NSE:TCS", "sector", "sector")
    with pytest.raises(DataIntegrityError, match="timezone-aware"):
        run_data_command(_args(*args, "--as-of", "2024-01-05T00:00:00"))
    with pytest.raises(DataIntegrityError, match="synthetic"):
        run_data_command(_args(*args, "--as-of", "2024-01-05T00:00:00Z"))
