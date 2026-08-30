import argparse
import json
from pathlib import Path

import pytest

from quantlab.data.cli import run_data_command
from quantlab.data.fabric.ingest import materialize_synthetic
from quantlab.data.fabric.layout import FabricLayout


def test_data_cli_list_and_pit_check(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("QUANT_LAB_DATA_DIR", str(tmp_path))
    layout = FabricLayout(tmp_path / "fabric")
    materialize_synthetic(layout, n_days=20)
    args = argparse.Namespace(data_cmd="list")
    assert run_data_command(args) == 0
    listed = json.loads(capsys.readouterr().out)
    assert listed[0]["dataset_id"] == "synthetic-nse"
    args = argparse.Namespace(data_cmd="pit-check", dataset="synthetic-nse", as_of="")
    assert run_data_command(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["rows"] > 0
