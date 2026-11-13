# Agent provider transport budgets

The shared `ProviderRunner` enforces a maximum of 6,000 requested output
tokens per attempt, at most two schema retries, a 120-second deadline and a
128,000-character combined prompt/JSON-schema ceiling. Individual callers can
and should set tighter budgets. Invalid requests fail before provider transport.

Each attempted call, including a schema retry, records its requested output-token
cap and prompt hash in the existing agent audit ledger.

An optional `ProviderBudgetPolicy` can be explicitly configured on a
`ProviderRunner` with positive integer task, family and UTC-day output-token-cap
limits. The durable policy is immutable: trying to reinstall the same values is
idempotent; different values are rejected rather than silently resetting usage.
There are no invented default budget limits. A runner can request that a policy
be mandatory with `require_budget=True`; missing policy blocks the call.
There is currently no supported policy adjustment or reservation reset for an
existing database. An explicit, audited owner-authorized policy-revision workflow
that preserves all previous reservations remains future work.

The owner can inspect or install a policy using the existing `quantlab agents`
CLI. No policy is installed by inspection or automatically, and no numeric limits
are suggested here:

```text
quantlab agents provider-budget-status
quantlab agents configure-provider-budget --task-output-tokens <positive-integer> --family-output-tokens <positive-integer> --daily-output-tokens <positive-integer>
```

Use the same Quant Lab data-directory configuration as the application. Inspect
the policy carefully before installing it: the family and task budgets are
**lifetime** limits and there is currently no supported reset or adjustment.
Policy installation is explicit and irrevocable for that database by this API.
Status reports limits and aggregate reserved caps, not actual usage or cost.
An unconfigured database retains the legacy behavior with no aggregate budget.

After configuration, all `ProviderRunner` instances using that database must
supply a host-chosen `budget_family_id`, otherwise they abstain. Current host
workflows provide stable scopes: strategy batches share a family by validated
exchange/symbol (across bar intervals); analyst, debate, and institution desk
calls share one desk family; desktop planning and explanation share another;
conceptual chat has its own. These are not taken from model responses, prompts,
credentials, or provider data. Distinct symbol aliases are not resolved into a
single economic security, so different aliases can have distinct budgets.
Other/custom callers must supply their own host-controlled family IDs. Family
limits aggregate forever, not per desk cycle; the daily limit resets at UTC
midnight. A policy is a local conservative safeguard, not spend tracking.

One atomic SQLite transaction checks and reserves the requested cap against all
three limits immediately before transport. The task scope is the run ID, the
family scope is a stable caller-supplied identifier across tasks, and the day is
UTC. Task and family accounting are lifetime within this database; a new family
identifier starts another family and is not a policy reset. Concurrent repository
instances and processes share the database counters. Repeated schema attempts
each reserve separately; timeouts, cancellation after reservation, persistence
errors after reservation, and crashes never refund, because a provider might
already have received the request. This can conservatively overcount attempts.

The reservation ledger stores hashed task/family IDs, prompt hash, timestamp and
requested cap; it does not store prompts, credentials or provider responses.
Separate agent databases do not share limits. These counters measure requested
output caps only: they are not actual input/output usage or monetary spend, and
they cannot prevent charges beyond the reported cap or outside this runner. A
provider may bill even when no usable response arrives. The database is not a
tamper-proof billing system and independent source usage remains unverified.
