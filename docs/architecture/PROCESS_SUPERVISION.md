# Process supervision

Logical services (app, data, research jobs, paper OMS, monitoring, shadow, safety, health, scheduler, audit writer) are supervised in-process. Restart policies: `NEVER | ON_FAILURE | EXPONENTIAL_BACKOFF | LIMITED_RESTARTS | MANUAL`. Crash-loop → `FAILED`/`HALTED`, not infinite restart. Restart must not duplicate paper/shadow cycles.
