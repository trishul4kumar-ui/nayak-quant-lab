from __future__ import annotations

import argparse
import json

import pytest

from quantlab.phase53.cli import run_phase53_command


def test_status_command_is_read_only_and_reports_no_go_evidence(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert run_phase53_command(argparse.Namespace(phase53_cmd="status")) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["state"] in {"BLOCKED", "EVIDENCE_INCOMPLETE", "READY_FOR_INDEPENDENT_REVIEW"}
    assert payload["live_trading"] is False
    assert payload["broker_write_enabled"] is False
    assert payload["execution_gateway_armed"] is False
