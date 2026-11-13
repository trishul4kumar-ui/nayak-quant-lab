# Fabric dataset version identity

The existing fabric ingestion path binds a dataset ID and version to its raw
checksum, source, data kind, filename, calendar, availability convention and
corporate-action/universe policies. A repeat with matching metadata is skipped
only when the recorded raw file still has the expected checksum and the prior
research-ready PIT files exist. A conflicting request or damaged raw file fails
without overwriting the registered version. The same bytes may be ingested under
a different dataset identity; a checksum match alone does not substitute an
unrelated catalog record. Unregistered partial artifacts are preserved for
inspection. Gate reports cannot be applied to another dataset identity/version.

These checks guard ingestion identity; they do not establish the licence,
historical availability, point-in-time completeness, market validity, or
profitability of the data. `RESEARCH_READY` remains the existing fabric gate
state and is not independent point-in-time certification. PIT integrity and
source/transform equivalence still require the separate research-reader checks.

Dataset, version and raw filename must be single path components; paths resolving
outside a fabric layer are rejected. New records also include a fingerprint of the
supplied bar objects. A repeated version with the same raw bytes but different bars
is rejected; older records lacking this fingerprint cannot be re-ingested in place.
This detects changed supplied bars, but the generic `ingest_bars` function accepts
both raw bytes and pre-parsed bars and does not establish their equivalence on the
first call. The CSV path parses its source and checks for changes during parsing;
independent source/PIT equivalence still requires the research-reader checks.

Fabric ingestions share a SQLite writer lock, released automatically if an ingest
process dies. The complete ingestion operation is not a single atomic transaction:
if it is interrupted before registration, unregistered artifacts are preserved and
block reuse of that version. Use a new version and investigate the prior artifacts
rather than deleting or silently repairing them. Direct calls to catalog upsert,
PIT-store writing, or other filesystem writers do not acquire this ingest lock;
the lock therefore guards cooperative ingest paths, not all possible modification
of an existing dataset. Restrict those writes or add a shared authorization and
integrity boundary before claiming universal immutability.

Ready gate reports must contain the full named set of required passing checks,
with no duplicate names, before they can change a matching catalog record's
state. This is a structural check, not a signature or independent verification;
trusted code can still construct misleading in-memory assertions.

Verification uses the data test suite with synthetic and simulated fixtures.
These tests establish software behavior only; no external source, broker account,
or live-market readiness was tested.
