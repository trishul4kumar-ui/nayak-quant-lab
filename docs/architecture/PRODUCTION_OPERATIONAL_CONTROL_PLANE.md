# Production operational control plane

**Version:** 2.6.0  
**Package:** `quantlab.ops`  
**Desktop:** Operations Control Lab (`ops`)

Operations platform for process supervision, config/env/secrets, health/readiness, backup/restore, clock/disk, release identity, and doctor. Not strategy, not OMS, not a broker.

`LIVE_TRADING` remains **false**. Fatal states do not auto-return to RUNNING. Unknown ≠ healthy.

See [PROCESS_SUPERVISION.md](PROCESS_SUPERVISION.md), [OBSERVABILITY.md](OBSERVABILITY.md), [BACKUP_RECOVERY.md](BACKUP_RECOVERY.md), [SECRETS_MANAGEMENT.md](SECRETS_MANAGEMENT.md), [FAILURE_RECOVERY.md](FAILURE_RECOVERY.md), [RELEASE_MANAGEMENT.md](RELEASE_MANAGEMENT.md), [../research/OPERATIONAL_READINESS.md](../research/OPERATIONAL_READINESS.md), [../decisions/ADR-040-production-operational-control-plane.md](../decisions/ADR-040-production-operational-control-plane.md).
