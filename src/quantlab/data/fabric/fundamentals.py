"""Fundamental observations. period_end is not available_time. Revisions are append-only."""

from __future__ import annotations

import base64
import binascii
import math
from datetime import date, datetime
from enum import StrEnum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from quantlab.control_plane.sqlite import ControlPlaneSqlite, ControlPlaneStoreError
from quantlab.core.errors import DataIntegrityError
from quantlab.data.fabric.checksums import sha256_bytes
from quantlab.data.fabric.types import DataKind
from quantlab.data.policy import require_real_data


class FundamentalObservation(BaseModel):
    security_id: str
    metric: str
    value: float
    period_start: date
    period_end: date
    publication_time: datetime
    available_time: datetime
    source: str
    revision: int = 1

    @model_validator(mode="after")
    def _period_is_not_availability(self) -> FundamentalObservation:
        if self.available_time.utcoffset() is None or self.publication_time.utcoffset() is None:
            raise ValueError("fundamental timestamps must be timezone-aware")
        if self.period_start > self.period_end or self.available_time < self.publication_time:
            raise ValueError("invalid period or availability before publication")
        if self.period_end > self.publication_time.date():
            raise ValueError("fundamental period ends after publication")
        if not math.isfinite(self.value) or self.revision < 1 or not self.source.strip():
            raise ValueError("invalid fundamental value, revision, or source")
        return self


class FundamentalStore:
    def __init__(self) -> None:
        self._rows: list[FundamentalObservation] = []

    def add(self, row: FundamentalObservation) -> None:
        # Validate again: model_copy(update=...) can bypass Pydantic validators.
        row = FundamentalObservation.model_validate(row.model_dump())
        key = (row.security_id, row.metric, row.period_end, row.available_time, row.revision)
        for existing in self._rows:
            if (
                existing.security_id,
                existing.metric,
                existing.period_end,
                existing.available_time,
                existing.revision,
            ) == key:
                if existing == row:
                    return
                raise DataIntegrityError("conflicting fundamental observation identity")
        self._rows.append(row.model_copy(deep=True))

    def as_of(
        self,
        security_id: str,
        metric: str,
        as_of: datetime,
    ) -> FundamentalObservation | None:
        if as_of.utcoffset() is None:
            raise ValueError("as_of must be timezone-aware")
        eligible = [
            row
            for row in self._rows
            if row.security_id == security_id
            and row.metric == metric
            and row.available_time <= as_of
        ]
        if not eligible:
            return None
        eligible.sort(key=lambda r: (r.period_end, r.available_time, r.revision))
        return eligible[-1].model_copy(deep=True)


class ReferenceKind(StrEnum):
    SECTOR = "sector"
    MARKET_CAP = "market_cap"
    FUNDAMENTAL = "fundamental"


class ReferenceObservation(BaseModel):
    """One source-supplied fact, including its effective and knowledge clocks."""

    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)

    security_id: str
    kind: ReferenceKind
    metric: str
    value: str | float
    unit: str
    effective_time: datetime
    publication_time: datetime
    available_time: datetime
    revision: int = Field(ge=1)
    period_end: date | None = None

    @field_validator("value", mode="before")
    @classmethod
    def _not_boolean(cls, value: object) -> object:
        if isinstance(value, bool):
            raise ValueError("boolean is not a reference value")
        return value

    @field_validator("security_id", "metric", "unit")
    @classmethod
    def _nonempty(cls, value: str) -> str:
        if not value.strip() or value != value.strip():
            raise ValueError("reference identifiers and unit must be non-empty and trimmed")
        return value

    @model_validator(mode="after")
    def _validate_fact(self) -> ReferenceObservation:
        if any(
            t.utcoffset() is None
            for t in (self.effective_time, self.publication_time, self.available_time)
        ):
            raise ValueError("reference timestamps must be timezone-aware")
        if self.available_time < self.publication_time:
            raise ValueError("availability cannot precede publication")
        if self.kind is ReferenceKind.SECTOR:
            if not isinstance(self.value, str) or not self.value.strip() or self.period_end:
                raise ValueError("sector needs a non-empty text value and no reporting period")
        elif not isinstance(self.value, float) or not math.isfinite(self.value):
            raise ValueError("numeric reference values must be finite numbers")
        elif self.kind is ReferenceKind.MARKET_CAP and (self.value <= 0 or self.period_end):
            raise ValueError("market cap must be positive and has no reporting period")
        elif self.kind is ReferenceKind.FUNDAMENTAL and self.period_end is None:
            raise ValueError("fundamentals require a period_end")
        if self.period_end is not None and self.period_end > self.publication_time.date():
            raise ValueError("reporting period cannot end after publication")
        return self


class ReferenceDataset(BaseModel):
    """A versioned source document; provenance is declared, not certified."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal["1"] = "1"
    dataset_id: str
    version: str
    source: str
    source_version: str
    data_kind: DataKind
    observations: tuple[ReferenceObservation, ...] = Field(min_length=1)

    @field_validator("dataset_id", "version", "source", "source_version")
    @classmethod
    def _nonempty(cls, value: str) -> str:
        if not value.strip() or value != value.strip():
            raise ValueError("reference source and identity must be non-empty and trimmed")
        return value

    @model_validator(mode="after")
    def _unique_facts(self) -> ReferenceDataset:
        if self.data_kind is DataKind.REAL and self.source.lower().startswith(
            ("synthetic", "mock", "memory_synthetic")
        ):
            raise ValueError("synthetic source cannot be labelled real")
        identities = [
            (
                r.security_id,
                r.kind,
                r.metric,
                r.period_end if r.kind is ReferenceKind.FUNDAMENTAL else r.effective_time,
                r.available_time,
                r.revision,
            )
            for r in self.observations
        ]
        if len(identities) != len(set(identities)):
            raise ValueError("ambiguous duplicate reference observation")
        return self


class ReferenceResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    dataset_id: str
    version: str
    source: str
    source_version: str
    source_checksum: str
    data_kind: DataKind
    as_of: datetime
    observation: ReferenceObservation


class ReferenceDataStore:
    """Immutable reference source documents in the existing control-plane store.

    Queries require a dataset version and a knowledge-time cutoff. This store
    does not independently verify a provider's declared historical clocks.
    """

    _namespace = "pit_reference_documents"

    def __init__(self, path: Path) -> None:
        self._store = ControlPlaneSqlite(path)

    def close(self) -> None:
        self._store.close()

    @staticmethod
    def _identity(dataset_id: str, version: str) -> str:
        # Length-prefixing prevents ambiguous dataset/version combinations.
        return f"{len(dataset_id)}:{dataset_id}:{version}"

    def ingest_json(self, raw: bytes) -> ReferenceDataset:
        """Validate and retain the exact source bytes under an immutable version."""
        try:
            dataset = ReferenceDataset.model_validate_json(raw)
        except ValueError as exc:
            raise DataIntegrityError("invalid point-in-time reference document") from exc
        require_real_data(dataset.data_kind.value, source=dataset.source)
        checksum = sha256_bytes(raw)
        payload = {"source_checksum": checksum, "raw_base64": base64.b64encode(raw).decode("ascii")}
        try:
            self._store.append(
                namespace=self._namespace,
                identity=self._identity(dataset.dataset_id, dataset.version),
                payload=payload,
                payload_hash=checksum,
                event="REFERENCE_DATASET_INGESTED",
            )
        except ControlPlaneStoreError as exc:
            raise DataIntegrityError(
                "reference dataset version conflict or storage failure"
            ) from exc
        return dataset

    def get_dataset(self, dataset_id: str, version: str) -> tuple[ReferenceDataset, str]:
        try:
            payload = self._store.get(self._namespace, self._identity(dataset_id, version))
        except (TypeError, ValueError) as exc:
            raise DataIntegrityError("reference dataset integrity check failed") from exc
        if payload is None:
            raise DataIntegrityError("reference dataset/version unavailable")
        try:
            raw = base64.b64decode(payload["raw_base64"], validate=True)
            checksum = str(payload["source_checksum"])
            if sha256_bytes(raw) != checksum:
                raise ValueError("source checksum mismatch")
            identity = self._identity(dataset_id, version)
            audit = [
                event
                for event in self._store.audit(self._namespace)
                if event["identity"] == identity
            ]
            if (
                len(audit) != 1
                or audit[0]["payload_hash"] != checksum
                or audit[0]["event"] != "REFERENCE_DATASET_INGESTED"
            ):
                raise ValueError("source audit checksum mismatch")
            dataset = ReferenceDataset.model_validate_json(raw)
            if (dataset.dataset_id, dataset.version) != (dataset_id, version):
                raise ValueError("dataset identity mismatch")
        except (KeyError, TypeError, ValueError, binascii.Error) as exc:
            raise DataIntegrityError("reference dataset integrity check failed") from exc
        return dataset, checksum

    def as_of(
        self,
        dataset_id: str,
        version: str,
        *,
        security_id: str,
        kind: ReferenceKind,
        metric: str,
        as_of: datetime,
        allow_synthetic: bool = False,
    ) -> ReferenceResult | None:
        if as_of.utcoffset() is None:
            raise ValueError("as_of must be timezone-aware")
        if not isinstance(kind, ReferenceKind):
            raise ValueError("kind must be a ReferenceKind")
        dataset, checksum = self.get_dataset(dataset_id, version)
        if dataset.data_kind is DataKind.SYNTHETIC and not allow_synthetic:
            raise DataIntegrityError("synthetic reference data is not eligible for real research")
        if dataset.data_kind is DataKind.SYNTHETIC:
            require_real_data(dataset.data_kind.value, source=dataset.source)
        eligible = [
            r
            for r in dataset.observations
            if r.security_id == security_id
            and r.kind is kind
            and r.metric == metric
            and r.effective_time <= as_of
            and r.available_time <= as_of
        ]
        if not eligible:
            return None
        if kind is ReferenceKind.FUNDAMENTAL:
            eligible.sort(key=lambda r: (r.period_end or date.min, r.available_time, r.revision))
        else:
            eligible.sort(key=lambda r: (r.effective_time, r.available_time, r.revision))
        return ReferenceResult(
            dataset_id=dataset_id,
            version=version,
            source=dataset.source,
            source_version=dataset.source_version,
            source_checksum=checksum,
            data_kind=dataset.data_kind,
            as_of=as_of,
            observation=eligible[-1],
        )
