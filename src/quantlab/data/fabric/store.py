"""Parquet + DuckDB PIT store. Queries never return available_time > as_of."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

from quantlab.core.errors import DataIntegrityError, LookAheadError
from quantlab.core.identifiers import InstrumentId
from quantlab.core.time import PointInTime, as_utc
from quantlab.data.fabric.layout import FabricLayout
from quantlab.domain.models import BarInterval, OHLCVBar

BAR_FIELDS = (
    "security_id",
    "exchange",
    "symbol",
    "event_time",
    "effective_time",
    "available_time",
    "ingestion_time",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "interval",
    "dataset_version",
    "source_id",
    "session_date",
    "price_kind",
    "data_kind",
)

_TS = pa.timestamp("us", tz="UTC")
BAR_SCHEMA = pa.schema(
    [
        ("security_id", pa.string()),
        ("exchange", pa.string()),
        ("symbol", pa.string()),
        ("event_time", _TS),
        ("effective_time", _TS),
        ("available_time", _TS),
        ("ingestion_time", _TS),
        ("open", pa.float64()),
        ("high", pa.float64()),
        ("low", pa.float64()),
        ("close", pa.float64()),
        ("volume", pa.float64()),
        ("interval", pa.string()),
        ("dataset_version", pa.string()),
        ("source_id", pa.string()),
        ("session_date", pa.string()),
        ("price_kind", pa.string()),
        ("data_kind", pa.string()),
    ]
)


def _to_datetime(value: object) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value
    to_pydatetime = getattr(value, "to_pydatetime", None)
    if callable(to_pydatetime):
        converted = to_pydatetime()
        return _to_datetime(converted)
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed
    raise TypeError(f"cannot parse datetime from {type(value)!r}")


def bars_to_table(bars: list[OHLCVBar]) -> pa.Table:
    columns: dict[str, list[object]] = {name: [] for name in BAR_FIELDS}
    for bar in bars:
        columns["security_id"].append(str(bar.instrument))
        columns["exchange"].append(bar.instrument.exchange)
        columns["symbol"].append(bar.instrument.symbol)
        columns["event_time"].append(as_utc(bar.pit.event_time))
        columns["effective_time"].append(as_utc(bar.pit.effective_time))
        columns["available_time"].append(as_utc(bar.pit.available_time))
        columns["ingestion_time"].append(as_utc(bar.pit.ingestion_time))
        columns["open"].append(bar.open)
        columns["high"].append(bar.high)
        columns["low"].append(bar.low)
        columns["close"].append(bar.close)
        columns["volume"].append(bar.volume)
        columns["interval"].append(bar.interval.value)
        columns["dataset_version"].append(bar.dataset_version)
        columns["source_id"].append(bar.source_id)
        columns["session_date"].append(bar.session_date)
        columns["price_kind"].append(bar.price_kind)
        columns["data_kind"].append(bar.data_kind)
    return pa.table(columns, schema=BAR_SCHEMA)


def table_to_bars(table: pa.Table) -> list[OHLCVBar]:
    if not isinstance(table, pa.Table):
        raise TypeError(f"expected pyarrow.Table, got {type(table)!r}")
    rows = table.to_pydict()
    n = table.num_rows
    bars: list[OHLCVBar] = []
    for i in range(n):
        event = _to_datetime(rows["event_time"][i])
        effective = _to_datetime(rows["effective_time"][i])
        available = _to_datetime(rows["available_time"][i])
        ingested = _to_datetime(rows["ingestion_time"][i])
        bars.append(
            OHLCVBar(
                instrument=InstrumentId(
                    exchange=str(rows["exchange"][i]),
                    symbol=str(rows["symbol"][i]),
                ),
                pit=PointInTime(
                    event_time=event,
                    effective_time=effective,
                    available_time=available,
                    ingestion_time=ingested,
                ),
                interval=BarInterval(str(rows["interval"][i])),
                open=float(rows["open"][i]),
                high=float(rows["high"][i]),
                low=float(rows["low"][i]),
                close=float(rows["close"][i]),
                volume=float(rows["volume"][i]),
                dataset_version=str(rows["dataset_version"][i]),
                source_id=str(rows["source_id"][i]),
                session_date=str(rows["session_date"][i]),
                price_kind=str(rows["price_kind"][i]),
                data_kind=str(rows["data_kind"][i]),
            )
        )
    return bars


def parquet_files(layout: FabricLayout, dataset_id: str, version: str) -> list[Path]:
    return sorted(layout.pit_dir(dataset_id, version).glob("year=*/bars.parquet"))


class PitStore:
    def __init__(self, layout: FabricLayout, dataset_id: str, version: str) -> None:
        self.layout = layout
        self.dataset_id = dataset_id
        self.version = version

    def write_bars(self, bars: list[OHLCVBar]) -> list[Path]:
        if not bars:
            raise DataIntegrityError("cannot write empty PIT parquet")
        by_year: dict[int, list[OHLCVBar]] = defaultdict(list)
        for bar in bars:
            by_year[as_utc(bar.pit.event_time).year].append(bar)
        written: list[Path] = []
        root = self.layout.pit_dir(self.dataset_id, self.version)
        for year, group in sorted(by_year.items()):
            folder = root / f"year={year}"
            folder.mkdir(parents=True, exist_ok=True)
            path = folder / "bars.parquet"
            pq.write_table(bars_to_table(group), path)
            written.append(path)
        self._register_view()
        return written

    def query(
        self,
        *,
        as_of: datetime,
        start: datetime | None = None,
        end: datetime | None = None,
        instruments: list[str] | None = None,
    ) -> list[OHLCVBar]:
        files = parquet_files(self.layout, self.dataset_id, self.version)
        if not files:
            raise DataIntegrityError(f"missing PIT parquet for {self.dataset_id} {self.version}")
        cutoff = as_utc(as_of)
        clauses = ["available_time <= CAST(? AS TIMESTAMPTZ)"]
        params: list[object] = [cutoff.isoformat()]
        if start is not None:
            clauses.append("event_time >= CAST(? AS TIMESTAMPTZ)")
            params.append(as_utc(start).isoformat())
        if end is not None:
            clauses.append("event_time <= CAST(? AS TIMESTAMPTZ)")
            params.append(as_utc(end).isoformat())
        if instruments:
            placeholders = ",".join(["?"] * len(instruments))
            clauses.append(f"security_id IN ({placeholders})")
            params.extend(instruments)
        sql = (
            f"SELECT {', '.join(BAR_FIELDS)} FROM read_parquet(?, hive_partitioning=true) WHERE "
            + " AND ".join(clauses)
            + " ORDER BY security_id, event_time"
        )
        con = duckdb.connect(str(self.layout.duckdb_path))
        try:
            rel = con.execute(sql, [[str(p) for p in files], *params])
            fetched = rel.arrow()
            table = fetched.read_all() if hasattr(fetched, "read_all") else fetched
        finally:
            con.close()
        bars = table_to_bars(table)
        for bar in bars:
            if bar.pit.available_time > cutoff:
                raise LookAheadError(
                    f"PIT query leaked {bar.instrument} "
                    f"available {bar.pit.available_time} > {cutoff}"
                )
        return bars

    def all_as_of(self, as_of: datetime) -> dict[InstrumentId, list[OHLCVBar]]:
        grouped: dict[InstrumentId, list[OHLCVBar]] = {}
        for bar in self.query(as_of=as_of):
            grouped.setdefault(bar.instrument, []).append(bar)
        return grouped

    def _register_view(self) -> None:
        files = parquet_files(self.layout, self.dataset_id, self.version)
        if not files:
            return
        view = f"pit_{_sql_ident(self.dataset_id)}_{_sql_ident(self.version)}"
        listed = ", ".join(_sql_quote(str(path)) for path in files)
        con = duckdb.connect(str(self.layout.duckdb_path))
        try:
            con.execute(
                f"CREATE OR REPLACE VIEW {view} AS "
                f"SELECT * FROM read_parquet([{listed}], hive_partitioning=true)"
            )
        finally:
            con.close()


def _sql_ident(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in value)
    return cleaned or "x"


def _sql_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"
