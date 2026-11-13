# Digital twin replay and checkpoint limits

The digital twin is a simulated scenario tool, not broker evidence. Replay now
requires an existing completed run, retains its original event time, and compares
snapshot, decision, portfolio, fill, account, reconciliation and aggregate state
hashes plus the ordered event chain. Run/event identifiers are intentionally not
compared because the replay has a new identity.

The twin's current checkpoint stores hashes, not a restorable source stream and
complete operating state. Consequently checkpoint recovery explicitly reports
that restoration is not implemented; two fresh matching runs are not evidence
that a checkpoint was restored. Twin storage is in memory, and this change does
not establish restart recovery, independent account reconciliation or sustained
shadow operation.
