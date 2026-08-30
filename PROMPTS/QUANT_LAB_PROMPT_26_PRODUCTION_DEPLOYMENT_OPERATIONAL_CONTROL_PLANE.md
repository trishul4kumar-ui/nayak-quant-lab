# QUANT LAB — PROMPT 26
# Production Deployment & Operational Control Plane
## Institutional-Grade Engineering Specification
### Target Release: QUANT LAB 2.6.0

---

## 0. Mission

Implement Prompt 26 as the **Production Deployment / Operational Control Plane** for QUANT LAB.

This engine makes the research, paper, shadow, and future controlled-live stack operationally reliable.

It must answer:

> **Is QUANT LAB running the correct version, with the correct configuration, data, state, processes, secrets, observability, backups, and recovery guarantees — and can the system detect and contain operational failure?**

Prompt 26 is an **operations platform**, not a trading strategy, broker, OMS, risk engine, or certification engine.

### Non-negotiable state

```text
LIVE_TRADING = FALSE
```

Prompt 26 must not activate live trading.

---

# 1. Architectural Position

```text
Research Engines
      ↓
Paper OMS
      ↓
Monitoring / Data / TCA
      ↓
Econometrics
      ↓
Certification
      ↓
Shadow Execution
      ↓
Prompt 25 Safety Gateway
      ↓
┌─────────────────────────────────────────┐
│ P26 PRODUCTION OPERATIONAL CONTROL PLANE│
│                                         │
│ PROCESS SUPERVISION                     │
│ CONFIGURATION                           │
│ SECRETS                                 │
│ HEALTH                                  │
│ OBSERVABILITY                           │
│ BACKUPS                                 │
│ RECOVERY                                │
│ INCIDENTS                               │
│ RELEASES                                │
│ AUDIT                                   │
└─────────────────────────────────────────┘
      ↓
Future Broker / Execution Infrastructure
```

Prompt 26 must not absorb the responsibilities of Prompts 05, 23, 25, or future broker adapters.

---

# 2. Operational Philosophy

Use institutional reliability principles:

```text
FAIL CLOSED
OBSERVE BEFORE ACT
IMMUTABLE AUDIT
DETERMINISTIC CONFIGURATION
EXPLICIT STATE
GRACEFUL DEGRADATION
NO SILENT RECOVERY
NO SILENT DATA LOSS
NO SILENT CONFIGURATION CHANGE
NO SECRET EXPOSURE
```

Operational status must distinguish:

```text
HEALTHY
DEGRADED
UNAVAILABLE
FAILED
HALTED
RECOVERY
UNKNOWN
```

Unknown must never mean healthy.

---

# 3. Core Responsibilities

Implement:

1. Process supervision
2. Service lifecycle
3. Configuration management
4. Environment validation
5. Secret management boundary
6. Health checks
7. Readiness checks
8. Liveness checks
9. Dependency checks
10. Structured logging
11. Metrics
12. Event tracing
13. Incident management
14. Backup management
15. Recovery management
16. State checkpointing
17. Release/version management
18. Configuration hashing
19. Auditability
20. Operational kill integration with Prompt 25
21. Resource monitoring
22. Disk/data integrity checks
23. Clock/time synchronization checks
24. Controlled startup/shutdown
25. Failure injection tests

---

# 4. Operational State Machine

Create an explicit state machine:

```text
BOOTING
↓
INITIALIZING
↓
CONFIG_VALIDATION
↓
DEPENDENCY_VALIDATION
↓
DATA_VALIDATION
↓
HEALTH_CHECK
↓
READY
↓
RUNNING
↓
DEGRADED
↓
HALTED
↓
RECOVERY
↓
READY
```

Fatal states must include:

```text
CONFIG_INVALID
SECRET_INVALID
DATA_CORRUPT
STATE_CORRUPT
DEPENDENCY_FAILED
CLOCK_INVALID
DISK_CRITICAL
AUDIT_FAILURE
RECONCILIATION_FAILURE
SAFETY_FAILURE
```

No automatic transition from fatal state to running.

---

# 5. Process Supervision

Create a process supervisor capable of managing logical services such as:

```text
quantlab.app
data service
research jobs
paper OMS
monitoring
shadow execution
health service
scheduler
audit writer
```

Do not create duplicate engines.

Each supervised process needs:

```text
process_id
service_name
version
pid
start_time
heartbeat
state
restart_count
exit_code
resource_usage
config_hash
binary/source identity
```

---

# 6. Restart Policy

Support explicit policies:

```text
NEVER
ON_FAILURE
EXPONENTIAL_BACKOFF
LIMITED_RESTARTS
MANUAL
```

A crash-loop must not continue indefinitely.

Suggested controls:

```text
max_restart_count
backoff_initial
backoff_max
stability_window
cooldown
```

After repeated failure:

```text
FAILED / HALTED
```

not endless restart.

---

# 7. Configuration Management

Create versioned, typed configuration.

Every operational run must bind to:

```text
config_id
config_version
config_hash
environment
software_version
schema_version
timestamp
```

Material configuration changes invalidate dependent operational state.

Do not allow runtime mutation of safety-critical configuration without an explicit controlled workflow.

---

# 8. Environment Separation

Support explicit environments:

```text
DEVELOPMENT
TEST
RESEARCH
PAPER
SHADOW
PRODUCTION
```

Production configuration must never be accidentally used in research.

Research credentials must never be interpreted as production credentials.

Environment identity must be visible in CLI, UI, logs, and audit records.

---

# 9. Secret Management

Implement a provider-neutral secret interface.

Example:

```text
SecretProvider
SecretReference
SecretMetadata
SecretAccessAudit
```

Do not hard-code secrets.

Do not print:

```text
API keys
API secrets
tokens
passwords
session cookies
private keys
account credentials
```

in:

```text
logs
exceptions
reports
CLI output
ledger
UI
snapshots
```

Secrets must be referenced by identifier, not copied into research artifacts.

Prompt 26 may validate secret availability but must not create broker credentials.

---

# 10. Secret Rotation

Support lifecycle metadata:

```text
created_at
expires_at
rotation_due
last_verified
provider
reference
status
```

Expired or unverifiable secrets must result in operational failure for services that require them.

Do not automatically rotate external credentials without an approved provider integration.

---

# 11. Health Model

Create layered health:

```text
SYSTEM
PROCESS
CONFIG
DATA
DATABASE
FILESYSTEM
CLOCK
AUDIT
RECONCILIATION
RESEARCH
PAPER_OMS
SHADOW
SAFETY
CERTIFICATION
```

Every component returns:

```text
PASS
WARN
FAIL
NOT_TESTED
```

Health must include provenance and timestamp.

---

# 12. Readiness vs Liveness

Separate:

### Liveness

> Is the process alive?

### Readiness

> Is the service safe and correctly initialized to perform its permitted role?

A process can be alive but not ready.

Example:

```text
process_alive = PASS
data_ready = FAIL
service_ready = FAIL
```

Never equate heartbeat with readiness.

---

# 13. Dependency Graph

Represent dependencies explicitly.

Example:

```text
Shadow Execution
    ↓
Paper OMS
    ↓
Execution Research
    ↓
PIT Data
    ↓
Filesystem / Catalog
```

and:

```text
Safety Gateway
    ↓
Certification
    ↓
Reconciliation
    ↓
Operational Health
```

A failed dependency must propagate appropriately.

Do not claim overall health if a critical dependency is unavailable.

---

# 14. Observability

Implement structured logs.

Each event should contain:

```text
event_id
timestamp
service
component
severity
event_type
run_id
request_id
correlation_id
environment
software_version
config_hash
message
structured_context
```

Severity:

```text
DEBUG
INFO
NOTICE
WARNING
ERROR
CRITICAL
```

No secrets.

---

# 15. Metrics

Create operational metrics for:

```text
process uptime
restart count
job duration
job failures
data freshness
data coverage
disk utilization
memory utilization
CPU utilization
queue depth
paper OMS latency
shadow loop latency
reconciliation status
safety status
certification status
audit write latency
backup age
backup success
recovery test status
```

Metrics must be timestamped and attributable.

---

# 16. Event Correlation

Support:

```text
request_id
run_id
experiment_id
decision_id
oms_run_id
shadow_run_id
authorization_id
incident_id
```

A complete event chain should be traceable:

```text
DATA SNAPSHOT
→ RESEARCH RUN
→ DECISION
→ TARGET
→ ORDER PLAN
→ PAPER/SHADOW RUN
→ MONITORING
→ SAFETY
→ OPERATIONAL EVENT
```

---

# 17. Operational Audit

Reuse the existing JSONL ledger where appropriate.

Do not create a competing research ledger.

Operational audit records should include:

```text
startup
shutdown
config change
version change
process restart
health failure
incident
backup
restore
secret verification
recovery
manual intervention
safety event
certification event
```

Audit failure must be treated as critical.

---

# 18. Backup Architecture

Implement backup abstractions for:

```text
configuration
research registry
SQLite catalog
knowledge graph
JSONL ledger
paper OMS state
shadow state
operational state
```

Never back up secrets in plaintext unless an explicitly secure provider mechanism exists.

Every backup should have:

```text
backup_id
created_at
source
size
checksum
schema_version
software_version
retention_class
status
```

---

# 19. Backup Integrity

Implement SHA-256 checksums.

Required states:

```text
CREATED
VERIFIED
CORRUPTED
EXPIRED
RESTORED
```

A backup that has never been verified must not be represented as recovery-ready.

---

# 20. Restore Workflow

Implement:

```text
DISCOVER
→ VERIFY
→ STAGE
→ VALIDATE
→ RESTORE
→ RECONCILE
→ HEALTH CHECK
→ READY
```

Never overwrite production state blindly.

Restores must create a recovery event and preserve previous state metadata.

---

# 21. Recovery Objectives

Define configuration fields:

```text
RPO
RTO
```

Do not invent a production SLA.

Allow the policy to specify targets.

Measure:

```text
observed_RPO
observed_RTO
```

against configured targets.

---

# 22. Disaster Recovery

Support recovery from:

- process crash
- machine reboot
- corrupted state
- partial ledger write
- interrupted paper run
- interrupted shadow run
- unavailable dependency
- disk pressure
- configuration corruption

Each scenario should have deterministic recovery behavior.

---

# 23. State Checkpointing

Critical long-running processes must support checkpoints.

Checkpoint:

```text
checkpoint_id
service
run_id
state_version
created_at
state_hash
config_hash
data_snapshot
```

Do not checkpoint mutable references without version identity.

---

# 24. Clock Safety

Financial systems are time-sensitive.

Implement clock checks for:

```text
system clock
timezone
UTC offset
IST conversion
monotonic clock
timestamp ordering
```

Detect:

```text
clock rollback
future timestamp
timestamp regression
unreasonable drift
```

A clock integrity failure must affect readiness of time-sensitive services.

Do not silently correct historical timestamps.

---

# 25. Resource Safety

Monitor:

```text
CPU
RAM
disk
inode usage
open files
process count
queue depth
database size
ledger growth
Parquet storage
```

Use policy thresholds:

```text
INFO
WARNING
CRITICAL
HALT
```

Never hard-code claims about production hardware capacity.

---

# 26. Disk Protection

Implement:

```text
minimum_free_space
critical_free_space
ledger_write_protection
snapshot_protection
backup_protection
```

If disk is critically low:

```text
HALT affected workload
PRESERVE audit
DO NOT delete research evidence automatically
```

No automatic deletion of research history.

---

# 27. Scheduler

Create a provider-neutral scheduler abstraction.

Jobs may include:

```text
health checks
data refresh
paper loop
shadow loop
monitoring
backup
reconciliation
reports
```

Every job requires:

```text
job_id
schedule
policy
timeout
retry policy
owner
enabled state
```

The scheduler must not create live orders.

---

# 28. Failure Handling

Implement typed operational failures:

```text
ConfigurationError
DependencyFailure
SecretUnavailable
ClockIntegrityError
DiskCapacityError
StateCorruptionError
BackupIntegrityError
RecoveryError
AuditFailure
HealthFailure
ProcessCrash
```

Errors must contain safe diagnostic context.

Never leak secrets.

---

# 29. Incident Management

Create:

```text
Incident
IncidentEvent
IncidentSeverity
IncidentStatus
IncidentTimeline
```

Severity:

```text
SEV-4 INFORMATIONAL
SEV-3 DEGRADED
SEV-2 MAJOR
SEV-1 CRITICAL
```

Do not automatically map business impact without evidence.

Incident lifecycle:

```text
OPEN
→ ACKNOWLEDGED
→ CONTAINED
→ RECOVERING
→ RESOLVED
→ POSTMORTEM
```

---

# 30. Operational Containment

Integrate with Prompt 25.

Examples:

```text
critical health failure
audit failure
reconciliation failure
data corruption
clock failure
state corruption
```

may request:

```text
SAFETY HALT
```

Prompt 26 must not directly place or cancel broker orders.

It may invoke the defined safety-control interface to request a controlled halt.

---

# 31. Release Management

Implement immutable release metadata:

```text
release_id
version
commit_sha
build_hash
config_schema
database_schema
python_version
dependency_lock_hash
created_at
environment
```

A release must be reproducible from recorded identity.

---

# 32. Dependency Manifest

Record dependency versions.

Detect unexpected dependency changes.

For safety-critical deployment:

```text
dependency drift → NOT_READY
```

Do not silently install arbitrary versions.

---

# 33. Startup Validation

Startup sequence:

```text
LOAD ENVIRONMENT
→ VERIFY VERSION
→ VERIFY CONFIG
→ VERIFY DEPENDENCIES
→ VERIFY CLOCK
→ VERIFY FILESYSTEM
→ VERIFY DATABASE
→ VERIFY DATA CATALOG
→ VERIFY LEDGER
→ VERIFY BACKUPS
→ VERIFY SAFETY STATE
→ VERIFY CERTIFICATION STATE
→ HEALTH CHECK
→ READY
```

Any critical failure stops readiness.

---

# 34. Controlled Shutdown

Shutdown must be explicit:

```text
QUIESCE
→ STOP NEW WORK
→ FINISH SAFE WORK
→ CHECKPOINT
→ FLUSH AUDIT
→ RECONCILE
→ CLOSE RESOURCES
→ SHUTDOWN
```

Do not terminate blindly.

---

# 35. Paper / Shadow Safety

Prompt 26 must preserve:

```text
PAPER
SHADOW
LIVE DISABLED
```

A deployment configuration cannot turn shadow into live.

No broker imports.

No live credentials.

No live routing.

---

# 36. Package Architecture

Create:

```text
src/quantlab/ops/
    __init__.py
    supervisor.py
    process.py
    lifecycle.py
    config.py
    environment.py
    secrets.py
    health.py
    readiness.py
    dependencies.py
    logging.py
    metrics.py
    tracing.py
    incidents.py
    backup.py
    restore.py
    recovery.py
    checkpoints.py
    clock.py
    resources.py
    scheduler.py
    release.py
    audit.py
    state.py
    policy.py
    repository.py
    service.py
    models.py
    errors.py
    integrity.py
    cli.py
```

Keep `__init__.py` thin.

---

# 37. Application Layer

Create:

```text
quantlab.app.ops
```

It exposes:

```text
system status
health
readiness
processes
incidents
backups
recovery
configuration
release
audit
resources
```

No Qt logic.

---

# 38. Desktop

Add **Operations Control Lab**.

Sections:

```text
System
Processes
Health
Readiness
Resources
Incidents
Backups
Recovery
Configuration
Release
Audit
```

Display clearly:

```text
ENVIRONMENT
VERSION
CONFIG HASH
HEALTH
READINESS
LIVE TRADING
SAFETY STATE
CERTIFICATION
RECONCILIATION
```

UI must not mutate safety-critical configuration directly.

---

# 39. CLI

Implement:

```text
quantlab ops status
quantlab ops health
quantlab ops readiness
quantlab ops processes
quantlab ops start
quantlab ops stop
quantlab ops restart
quantlab ops incidents
quantlab ops backups
quantlab ops backup
quantlab ops verify-backup
quantlab ops restore
quantlab ops recovery
quantlab ops checkpoint
quantlab ops config
quantlab ops release
quantlab ops resources
quantlab ops clock
quantlab ops audit
quantlab ops doctor
```

---

# 40. Integrity Flags

Add:

```text
configuration_mutation
configuration_hash_mismatch
unexpected_dependency
secret_exposure
secret_expired
clock_rollback
future_timestamp
timestamp_regression
audit_write_failure
backup_checksum_failure
restore_without_validation
state_checkpoint_mismatch
state_corruption
process_identity_mismatch
release_identity_mismatch
environment_confusion
production_config_in_research
research_config_in_production
unsafe_restart
restart_loop
health_false_positive
readiness_false_positive
silent_recovery
silent_data_loss
operational_bypass
safety_halt_failure
```

Rules:

```text
None → NOT_TESTED
Direct integrity violation → FAIL
Unknown critical state → NOT_READY
```

---

# 41. Tests

Create:

```text
tests/ops/
    test_supervisor.py
    test_lifecycle.py
    test_config.py
    test_environment.py
    test_secrets.py
    test_health.py
    test_readiness.py
    test_dependencies.py
    test_logging.py
    test_metrics.py
    test_incidents.py
    test_backup.py
    test_restore.py
    test_recovery.py
    test_checkpoint.py
    test_clock.py
    test_resources.py
    test_scheduler.py
    test_release.py
    test_audit.py
    test_integrity.py
    test_failure_injection.py
    test_cli.py
```

Mandatory tests:

1. Process crash is detected.
2. Crash-loop is contained.
3. Configuration hash changes are detected.
4. Environment confusion is rejected.
5. Secret values never appear in logs.
6. Expired secrets produce failure.
7. Clock rollback is detected.
8. Future timestamps are rejected.
9. Corrupt backup fails verification.
10. Unverified backup cannot be marked recovery-ready.
11. Restore requires validation.
12. Audit failure affects readiness.
13. Disk-critical state is detected.
14. State checkpoint mismatch is detected.
15. Release identity mismatch is detected.
16. Safety halt integration works.
17. Shutdown flushes audit state.
18. Restart does not duplicate paper/shadow runs.
19. Operational retries are bounded.
20. Scheduler cannot invoke live trading.
21. UI cannot bypass application services.
22. No broker imports.
23. `LIVE_TRADING=false` remains enforced.

---

# 42. Failure Injection

Build controlled tests for:

```text
process crash
database unavailable
catalog corruption
ledger write failure
disk full
clock rollback
configuration corruption
dependency unavailable
backup corruption
restore failure
checkpoint corruption
safety service unavailable
certification unavailable
reconciliation failure
```

The expected behavior must be explicit.

---

# 43. Verification

Run:

```text
pytest tests/ops
ruff check <owned paths>
mypy --strict <owned paths>
```

Regression:

```text
safety
shadow
paper_oms
capital
monitoring
tca
data
certification
knowledge
integrity
UI smoke
```

Expected:

```text
LIVE_TRADING = false
BROKER_IMPORTS = 0
NO_SECRET_LEAKS
NO_SILENT_RECOVERY
NO_SILENT_DATA_LOSS
```

---

# 44. Documentation

Create:

```text
docs/architecture/PRODUCTION_OPERATIONAL_CONTROL_PLANE.md
docs/architecture/PROCESS_SUPERVISION.md
docs/architecture/OBSERVABILITY.md
docs/architecture/BACKUP_RECOVERY.md
docs/architecture/SECRETS_MANAGEMENT.md
docs/architecture/FAILURE_RECOVERY.md
docs/architecture/RELEASE_MANAGEMENT.md
docs/research/OPERATIONAL_READINESS.md
docs/decisions/ADR-039-production-operational-control-plane.md
```

Update:

```text
README
BACKLOG
LOCAL_RUN
architecture map
health registry
CLI docs
deployment documentation
```

---

# 45. Forbidden Shortcuts

Do NOT:

- embed broker integration
- place orders
- cancel live orders
- create live credentials
- print secrets
- silently restart forever
- silently delete research evidence
- auto-repair corrupted state
- mark unverified backups as valid
- treat process liveness as readiness
- treat WARN as PASS
- treat UNKNOWN as HEALTHY
- bypass Prompt 25
- bypass Prompt 23
- create a second ledger
- create a second data fabric
- create a second risk engine
- create a second backtester

---

# 46. Completion Criteria

Prompt 26 is complete only when:

```text
[ ] Process supervisor implemented
[ ] Explicit operational state machine
[ ] Configuration/version hashing
[ ] Environment separation
[ ] Secret abstraction
[ ] Health + readiness
[ ] Dependency graph
[ ] Structured logs
[ ] Metrics
[ ] Correlation IDs
[ ] Incident management
[ ] Backup system
[ ] Backup verification
[ ] Restore workflow
[ ] Recovery workflow
[ ] Checkpointing
[ ] Clock integrity
[ ] Resource monitoring
[ ] Scheduler
[ ] Release identity
[ ] Failure injection
[ ] Safety integration
[ ] Operations Control Lab
[ ] CLI
[ ] Integrity flags
[ ] No broker imports
[ ] LIVE_TRADING=false
[ ] Existing engines intact
[ ] Regression tests pass
[ ] ruff clean on owned paths
[ ] mypy strict clean on owned paths
[ ] Documentation complete
```

### Final Principle

> **A production trading system is not production-ready because the strategy works; it is production-ready only when its failures are observable, bounded, recoverable, auditable, and unable to silently cross the safety boundary.**

Prompt 26 is operational infrastructure. It does not grant trading authority.
