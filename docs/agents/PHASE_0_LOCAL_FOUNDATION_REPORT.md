# Phase 0 — Local foundation

The existing typed research-agent provider interface now has an explicit Ollama adapter. Opt in
with `QUANT_LAB_AGENT_PROVIDER=ollama`; its default model is `qwen3:4b` and its host is
`http://127.0.0.1:11434`. The adapter accepts only a bare loopback host and port, has no cloud
fallback, accepts no broker credentials, and cannot access agent tools or broker functions.

Every request uses the existing fixed safety policy, frozen evidence boundary, Pydantic JSON
schema, output cap, deadline, local response-size limit, and host-side schema validation. Invalid
JSON, malformed replies, explicit refusal, provider errors, and timeout all fail closed. Untrusted
document text remains a user-message section and cannot alter the system policy.

On the development host, Ollama `0.40.1` is installed at
`/Applications/Ollama.app`, its service is bound to `127.0.0.1:11434`, and
`qwen3:4b` was pulled successfully (2.5 GB). A bounded structured-output localhost smoke check
passed on 2026-10-08. That check used no market data, broker credentials, or order action. It does
not establish research quality, financial suitability, strategy validity, or trading readiness.

Use `agents provider-health` before any research run; an unavailable provider blocks that run
rather than falling back. The local adapter remains research-only even while Ollama is available.
