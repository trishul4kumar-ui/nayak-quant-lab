# Point-in-time calendar reference

`quantlab.data.fabric.calendar` supports calendar snapshots with an exchange,
segment, source, source SHA-256, publication and availability times, coverage,
timezone, regular hours, holidays and explicit special-session hours. A source
revision is registered with its bytes; a checksum mismatch or empty source is
rejected. Snapshot selection uses only revisions available by the requested
decision time and rejects ambiguous revisions or missing date coverage.

`PointInTimeCalendar.session_as_of` returns the session known at a cutoff, or
raises when the reference is unavailable. A registered revision can be bound to
the existing `TradingCalendar` interface for consumers such as timestamp parsing.
The bound view records its version, source and checksum. Historical simulations
must use the calendar known at each individual decision time; binding a later
revision once for an earlier history would introduce look-ahead.

The calendar assumes weekdays are regular sessions within the declared coverage
except for supplied holidays, and treats weekends as closed except for explicit
special sessions. No official exchange calendar is bundled. Correctness depends
on a complete, authorized source and an honest extraction of the recorded dates
and hours. The checksum verifies the supplied raw bytes against the declaration;
it does not independently prove the extraction, source authenticity, licence or
historical knowledge timestamps. A date-only bar's inferred session-close time is
not independent evidence that the bar was actually available at that time.

The revision registry defaults to memory. Providing `storage_path` to
`PointInTimeCalendar` stores versioned revisions and exact source bytes in the
existing control-plane SQLite database; reopening recovers revisions and validates
their metadata, source checksum, identity and audit hash before a query or source
retrieval. Duplicate/conflicting versions fail closed. `source_bytes(version)`
returns the exact checked source. A surviving audit entry with a missing snapshot
also fails closed instead of falling back to an older revision. As with the existing control-plane store, a
party able to rewrite both records and audit entries can forge them: this is not
external cryptographic authentication. Stored source snapshots default to the
synthetic data-kind label for backwards compatibility; production must explicitly
supply `DataKind.REAL` and a non-synthetic source, while synthetic snapshots are
limited to isolated fixture runs. These labels are assertions, not licence checks.

There is no automatic provider adapter or integration into every research/portfolio
job. Unavailable coverage fails closed rather than falling back to the weekday
calendar. Tests use synthetic fixtures and do not certify exchange data.

The daily desk's existing sourced-calendar path uses the source's session open
and close rather than assuming regular hours for every date. A special session or
half day must supply explicit hours; otherwise classification fails rather than
guessing. Sourced calendars still require independent provenance and complete
historical coverage; the desk calendar interface alone does not establish those.
