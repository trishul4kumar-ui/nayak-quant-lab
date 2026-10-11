# Local Ollama Qwen3 foundation

Phase 0 adds an explicit local provider option for the existing typed research-agent interface.
Set `QUANT_LAB_AGENT_PROVIDER=ollama` to select it; its default model is `qwen3:4b` and its
default host is `http://127.0.0.1:11434`. The provider accepts only an explicit loopback host
and port, uses Ollama's non-streaming `/api/chat` structured-output format, requests no thinking
output, and has no cloud fallback.

The model receives the existing fixed system policy separately from role/task/frozen context and
untrusted evidence. Its response must validate against the host's Pydantic JSON contract. Invalid
JSON, refusal, timeout, malformed responses, or an unavailable Ollama process produce a safe
research failure. No broker credentials, order tools, or live authority are configured or exposed.

This is local research infrastructure, not proof of model quality, profitability, model
availability, market-data entitlement, or any authority to trade.
