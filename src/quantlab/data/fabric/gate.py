"""Dataset research gate. A file on disk is not RESEARCH_READY."""

from __future__ import annotations

from pydantic import BaseModel, Field

from quantlab.data.fabric.catalog import DatasetRecord
from quantlab.data.fabric.quality import DataQualityReport
from quantlab.data.fabric.types import DataKind, DatasetState
from quantlab.domain.research import CheckResult


class GateVerdict(BaseModel):
    name: str
    result: CheckResult
    required: bool
    note: str = ""


class ResearchGateReport(BaseModel):
    dataset_id: str
    version: str
    data_kind: DataKind
    checks: list[GateVerdict] = Field(default_factory=list)
    research_ready: bool = False

    def as_str_map(self) -> dict[str, str]:
        return {item.name: item.result.value for item in self.checks}

    def result_for(self, name: str) -> CheckResult | None:
        for item in self.checks:
            if item.name == name:
                return item.result
        return None


def _verdict(name: str, result: CheckResult, *, required: bool, note: str = "") -> GateVerdict:
    return GateVerdict(name=name, result=result, required=required, note=note)


def evaluate_research_gate(
    record: DatasetRecord,
    *,
    quality: DataQualityReport | None = None,
    pit_verified: bool | None = None,
    timezone_defined: bool = True,
    identity_present: bool = True,
) -> ResearchGateReport:
    checks: list[GateVerdict] = []

    source_ok = bool(record.source.strip())
    checks.append(
        _verdict(
            "source_known",
            CheckResult.PASS if source_ok else CheckResult.FAIL,
            required=True,
            note=record.source or "missing source",
        )
    )

    checksum_ok = len(record.checksum) == 64 and all(
        c in "0123456789abcdef" for c in record.checksum
    )
    checks.append(
        _verdict(
            "checksum_recorded",
            CheckResult.PASS if checksum_ok else CheckResult.FAIL,
            required=True,
            note="sha256" if checksum_ok else "checksum missing or not sha256 hex",
        )
    )

    schema_ok = bool(record.schema_name.strip())
    checks.append(
        _verdict(
            "schema_validated",
            CheckResult.PASS if schema_ok else CheckResult.FAIL,
            required=True,
            note=record.schema_name or "no schema name",
        )
    )

    checks.append(
        _verdict(
            "timezone_defined",
            CheckResult.PASS if timezone_defined else CheckResult.FAIL,
            required=True,
            note="Asia/Kolkata session / UTC storage" if timezone_defined else "naive timestamps",
        )
    )

    if record.calendar_version:
        cal_result = CheckResult.PASS
        cal_note = record.calendar_version
        if "not_official" in record.notes or record.calendar_version.startswith("weekday"):
            cal_result = CheckResult.WARN
            cal_note = "weekday calendar is not an official NSE holiday file"
    else:
        cal_result = CheckResult.WARN
        cal_note = "no calendar version recorded"
    checks.append(_verdict("trading_calendar", cal_result, required=False, note=cal_note))

    checks.append(
        _verdict(
            "instrument_identity",
            CheckResult.PASS if identity_present else CheckResult.FAIL,
            required=True,
        )
    )

    if quality is None:
        ohlc = CheckResult.NOT_TESTED
        ohlc_note = "quality report not supplied"
        ohlc_required = True
    elif quality.invalid_count > 0 or quality.rows_accepted == 0:
        ohlc = CheckResult.FAIL
        ohlc_note = f"invalid={quality.invalid_count} accepted={quality.rows_accepted}"
        ohlc_required = True
    else:
        ohlc = CheckResult.PASS
        ohlc_note = f"accepted={quality.rows_accepted}"
        ohlc_required = True
    checks.append(_verdict("ohlc_valid", ohlc, required=ohlc_required, note=ohlc_note))

    policy = record.corporate_action_policy.strip() or "none"
    if policy in {"none", ""}:
        ca = CheckResult.NOT_TESTED
        ca_note = "no corporate-action file; not a silent PASS"
    else:
        ca = CheckResult.PASS
        ca_note = policy
    checks.append(_verdict("corporate_actions", ca, required=False, note=ca_note))

    if pit_verified is True:
        pit = CheckResult.PASS
        pit_note = "as_of filter holds for probe query"
    elif pit_verified is False:
        pit = CheckResult.FAIL
        pit_note = "PIT probe leaked or failed"
    else:
        pit = CheckResult.NOT_TESTED
        pit_note = "PIT not verified; file-on-disk is not enough"
    checks.append(_verdict("pit_verified", pit, required=True, note=pit_note))

    if record.universe_version:
        surv = CheckResult.PASS
        surv_note = record.universe_version
    else:
        surv = CheckResult.NOT_TESTED
        surv_note = "universe membership history not supplied"
    checks.append(_verdict("survivorship_verified", surv, required=False, note=surv_note))

    provenance_ok = source_ok and checksum_ok
    checks.append(
        _verdict(
            "provenance_complete",
            CheckResult.PASS if provenance_ok else CheckResult.FAIL,
            required=True,
            note=record.snapshot_id,
        )
    )

    if record.data_kind is DataKind.SYNTHETIC:
        checks.append(
            _verdict(
                "synthetic_not_live_grade",
                CheckResult.WARN,
                required=False,
                note="synthetic bars are architecture fixtures, not NSE history",
            )
        )

    ready = all(item.result is CheckResult.PASS for item in checks if item.required)
    return ResearchGateReport(
        dataset_id=record.dataset_id,
        version=record.version,
        data_kind=record.data_kind,
        checks=checks,
        research_ready=ready,
    )


def apply_gate_state(record: DatasetRecord, report: ResearchGateReport) -> DatasetRecord:
    if record.state is DatasetState.QUARANTINED:
        return record
    state = DatasetState.RESEARCH_READY if report.research_ready else DatasetState.NOT_READY
    return record.model_copy(update={"state": state})
