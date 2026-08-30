# Ingest and research gate

```text
source → raw (immutable) + sha256 → normalize → validate
  → Parquet → DuckDB → PIT query (available_time <= as_of)
```

## CLI

```bash
quantlab data list
quantlab data inspect <dataset>
quantlab data validate <dataset>
quantlab data ingest synthetic
quantlab data ingest path/to/nse.csv --dataset-id my-nse --version v1 --kind real
quantlab data status
quantlab data pit-check <dataset>
```

A user-supplied CSV is the **only** path for real Indian-market prints. This repository does not bundle NIFTY history or official holidays.

## Research gate

Required FAIL if any of these are missing: source, checksum, schema, timezone, instrument identity, valid OHLC, PIT probe.

Corporate actions and survivorship are `NOT_TESTED` until membership/CA files exist. `NOT_TESTED` is never rewritten as `PASS`.

`RESEARCH_READY` is a catalog state after the gate. Copying a file into `data/raw` is not enough.
