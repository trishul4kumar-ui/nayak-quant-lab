# AI Desk production-shadow runbook

Keep real market data, read-only broker observations, shadow orders, and simulated fills visibly
separate. On disconnect, stale data, mapping failure, reconciliation mismatch, provider outage,
or replay mismatch: fail closed, surface an incident, and create no new live pathway.
