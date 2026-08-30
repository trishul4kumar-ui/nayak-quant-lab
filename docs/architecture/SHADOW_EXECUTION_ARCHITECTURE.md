# Shadow Execution Architecture

**Version:** 2.4.0

A shadow cycle freezes a PIT snapshot, asks Prompt 17/18 for Δq intents and paper fills, then records a parallel `ShadowOrder` / `ShadowFill` / `SHADOW_POSITION` book.

Identity is hashed from strategy version, decision time, snapshot, portfolio state, and configuration. Duplicate keys return the prior cycle; they do not emit a second order stream.

Replay compares frozen hashes and reports `MATCH` or `MISMATCH`. A mismatch is retained, not overwritten.

Broker adapters, live routers, and live submitters are not part of this package and must not be imported.
