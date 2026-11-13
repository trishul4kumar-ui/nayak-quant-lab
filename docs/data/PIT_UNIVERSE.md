# Point-in-time universe membership

`PointInTimeUniverse` requires every supplied membership row in the requested universe to include a stable `membership_id`, `security_id`, source, effective interval, and timezone-aware `available_time`. Rows sharing a membership ID are revisions: the latest one available at the decision cutoff controls that membership, including corrections to its effective interval or cancellation. A revision not yet available cannot alter an earlier answer. Rows for another universe are ignored.

Unknown availability, missing source/identity, invalid intervals, conflicting same-time revisions, overlapping active memberships for one security and missing master records fail closed. Results are ordered by security ID. The input list is snapshotted; this is an in-memory query boundary, not a durable vendor-data store.

The membership records supplied to the query must themselves come from an authorized, version-pinned source. An empty result does **not** prove a complete historical universe. The existing instrument master does not yet version the availability of listing, delisting and symbol-history facts, and its current symbol can be a modern label; therefore a returned instrument is not evidence that its label or listing facts were historically knowable. No official NSE/index history or independent point-in-time certification is supplied by this module.
