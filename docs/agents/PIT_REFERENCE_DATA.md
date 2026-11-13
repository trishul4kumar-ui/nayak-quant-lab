# Point-in-time sector, market-cap and fundamental references

`quantlab.data.fabric.fundamentals.ReferenceDataStore` extends the existing
fundamental-data boundary with versioned source documents, using the existing
SQLite control-plane repository. It retains the exact JSON source bytes, their
SHA-256 checksum, a source name/version, data kind and immutable dataset/version
identity. Reusing a version with different source bytes fails. Loading verifies
the source checksum, identity and matching audit record. This detects accidental
corruption; it is not cryptographic authentication against a writer with control
of both data and audit tables.

The JSON document includes `dataset_id`, `version`, `source`, `source_version`,
`data_kind`, and nonempty `observations`. Each observation specifies a stable
security ID, kind (`sector`, `market_cap`, or `fundamental`), metric, typed
value, unit, effective, publication and availability timestamps, revision, and
for fundamentals a reporting period end. All timestamps must include an offset;
availability cannot precede publication. A sector value is text; market cap is
positive and numeric; fundamental values are finite and have a period end.

An isolated-test document has the following shape. The example is deliberately
synthetic and is not a market-data source:

```json
{
  "schema_version": "1",
  "dataset_id": "fixture-reference",
  "version": "v1",
  "source": "synthetic_fixture",
  "source_version": "v1",
  "data_kind": "synthetic",
  "observations": [
    {
      "security_id": "SYNTH:NSE:EXAMPLE",
      "kind": "sector",
      "metric": "sector",
      "value": "EXAMPLE",
      "unit": "classification",
      "effective_time": "2024-01-01T00:00:00+00:00",
      "publication_time": "2024-01-02T00:00:00+00:00",
      "available_time": "2024-01-03T00:00:00+00:00",
      "revision": 1,
      "period_end": null
    }
  ]
}
```

The `as_of` call requires dataset ID, exact version, security ID, kind, metric
and a timezone-aware cutoff. It excludes facts with future effective or
availability times. Sector and cap queries use the latest effective eligible
fact and its latest available revision; fundamental queries use the latest
eligible reporting period, then its latest available revision. Missing facts
return `None`; missing/corrupt datasets fail. Results include the exact source,
source version, raw checksum and data-kind label. Synthetic data is accepted
only by isolated fixture runs and must be explicitly requested by the caller.

These checks are software evidence, not a guarantee that the vendor-provided
availability or publication times are historically accurate, that the user has
a valid licence, that the data covers all needed securities/revisions, or that
the dataset is certified. The JSON document is loaded in full for each query;
it is an incremental local research interface, not a high-volume production
reference-data service. No real sector, cap, or fundamental history is bundled.
Real consumers must bind decisions to a verified source document and handle
missing reference values as unknown. Existing portfolio/factor readiness gates
must not be promoted merely because this storage mechanism exists.

User-supplied reference JSON can be imported through the existing data command:

```text
quantlab data reference-ingest /path/to/authorized-reference.json
quantlab data reference-query DATASET VERSION SECURITY_ID sector sector --as-of 2024-01-10T00:00:00Z
```

Import records the checksum and returns `STORED_UNCERTIFIED`; query requires an
explicit version and timezone-aware cutoff and returns `OBSERVED_UNCERTIFIED` or
`NOT_FOUND`. A document's source, licence and knowledge clocks remain claims to
verify separately. Synthetic fixture queries require the private isolated-test
environment as well as the explicit test-only option; there is no production
synthetic fallback.

The older in-memory `FundamentalStore` now validates publication order, keeps
defensive copies, rejects conflicting duplicate facts, and prioritizes the latest
reporting period over a newer revision to an older period.

The existing portfolio `exposure_report` can optionally accept a
`SectorReferenceInput` with the exact dataset ID/version, an aware decision time,
and an explicit portfolio-instrument-to-security-ID mapping. It calculates gross
weight by sector only when every held position has a classification known at the
cutoff. Missing mappings or facts produce `NOT_TESTED` with no partial aggregate;
complete calculations remain `WARN` because source completeness and historical
timestamps have not been independently verified. This is an optional research
diagnostic, not an enforced sector limit or automatic pipeline-wide integration.

The universe interface requires both effective membership revisions and explicit
point-in-time instrument-master revisions. Current security-master records alone
cannot supply historical listing, delisting, or ticker evidence. Instrument
revisions and membership history are currently in memory; their sources and
availability clocks are declared by the caller, not independently certified.
The corporate-action helper applies only known and effective split revisions.
Missing action coverage cannot be detected from an incomplete action list alone.

The research gate now treats omitted PIT evidence as `NOT_TESTED`. The AI desk's
new adjudication policy requires a separate canonical validation measurement for
PIT evidence; other passing validation measurements do not substitute for it.
Until an adapter supplies that evidence, the desk abstains. Old frozen
adjudication artifacts predate this required measurement and cannot be assumed to
replay under the new policy as if they had it. This does not certify any current
reference source.
