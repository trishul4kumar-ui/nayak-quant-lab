from quantlab.data.fabric.catalog import DatasetRecord
from quantlab.data.fabric.gate import evaluate_research_gate
from quantlab.data.fabric.quality import DataQualityReport
from quantlab.data.fabric.types import DataKind, DatasetState
from quantlab.domain.research import CheckResult


def _record(**overrides: object) -> DatasetRecord:
    payload: dict[str, object] = {
        "dataset_id": "nse-user",
        "version": "v1",
        "state": DatasetState.CURATED,
        "data_kind": DataKind.REAL,
        "source": "user.csv",
        "checksum": "a" * 64,
        "schema_name": "ohlcv_csv_v1",
        "corporate_action_policy": "none",
    }
    payload.update(overrides)
    return DatasetRecord.model_validate(payload)


def test_missing_checksum_fails_and_is_not_ready() -> None:
    report = evaluate_research_gate(
        _record(checksum=""),
        quality=DataQualityReport(rows_ingested=10, rows_accepted=10),
        pit_verified=True,
    )
    assert report.result_for("checksum_recorded") is CheckResult.FAIL
    assert report.research_ready is False


def test_corporate_actions_not_tested_is_never_pass() -> None:
    report = evaluate_research_gate(
        _record(),
        quality=DataQualityReport(rows_ingested=10, rows_accepted=10),
        pit_verified=True,
    )
    assert report.result_for("corporate_actions") is CheckResult.NOT_TESTED
    assert report.result_for("corporate_actions") is not CheckResult.PASS
    assert report.result_for("survivorship_verified") is CheckResult.NOT_TESTED
    assert report.research_ready is True


def test_unverified_pit_blocks_research_ready() -> None:
    report = evaluate_research_gate(
        _record(),
        quality=DataQualityReport(rows_ingested=10, rows_accepted=10),
        pit_verified=None,
    )
    assert report.result_for("pit_verified") is CheckResult.NOT_TESTED
    assert report.research_ready is False
