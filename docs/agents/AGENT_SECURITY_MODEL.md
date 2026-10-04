# Agent security model — phase 39

`quantlab.ai.permissions` is the single capability registry. Legacy default grants
are preserved. All live writes, execution authorization, risk/research overrides,
release certification, kill-switch clearing, secret reading and arbitrary execution
are permanently denied even if a caller supplies them as explicit grants. Agent
mandates containing those grants are rejected before a run.

Run contexts bind snapshot, scope, agent/model identities, tool policy, timestamps,
data kind and research mode. The original legacy snapshot is copied to canonical
JSON to prevent shallow mutation. Historical frames require explicit snapshot
binding and point-in-time timestamps; a quote snapshot never becomes price history.
REAL classification requires an explicit production manifest and matching provider
source rows. Unknown or mixed provenance is rejected, not upgraded to REAL. History
must also match the declared data kind and price basis, and be ingested by `as_of`.

Tools accept enumerated names and typed arguments only. There is no shell, Python,
SQL or URL argument. Registered tools call canonical engines and return narrow
evidence DTOs. Unbound tools return UNAVAILABLE; missing history returns NOT_TESTED.
Neither means PASS. Attempt budgets survive restart and denied requests are audited.
Gateway locking is per instance; this phase does not claim a cross-process scheduler
or atomic multi-worker quota reservations. Add those before orchestration allows
multiple workers for one run context.

Provider prompts separate fixed system policy from role, task, frozen context and
untrusted evidence. Credentials are used only by transport and are never put in
prompts, audit, or presentation payloads. Raw provider text is not persisted or
logged. Provider exceptions become safe codes. Structured output must validate
locally even when the remote API promises schema adherence.

Cancellation and deadline terminate result consumption, not an already dispatched
HTTP request. A running transport retains its semaphore until it finishes, preventing
overlapping retries. Only schema errors have a bounded retry; network failures do not.

The optional local WebChannel exposes exactly one navigation slot. It only accepts
known agents or published evidence identities. It receives composed presentation
DTOs and cannot access domain tools or execution. Native inspectors remain usable
without Chromium. No real order control exists in the foundation page.
The web profile is off-the-record with memory-only cache. Requests/navigation are
restricted to the bundled asset directory and the Qt WebChannel resource; external
URLs and local files outside that directory are blocked. WebGL absence or renderer
failure does not alter domain authority.

Python package boundaries are a capability design, not an operating-system sandbox.
An already-compromised Python process has workspace permissions; future production
execution must retain a separate service/process trust boundary.
