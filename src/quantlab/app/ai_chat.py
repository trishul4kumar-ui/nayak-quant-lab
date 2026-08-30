"""AI research chat — rule-based NAYAK with optional OpenAI when keyed."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass

from quantlab.ai.permissions import AiCapability, AiPermissions
from quantlab.app.assistant import NayakAssistant
from quantlab.app.bootstrap import ApplicationRuntime


@dataclass(frozen=True)
class AiChatStatus:
    provider: str
    connected: bool
    detail: str


def ai_status() -> AiChatStatus:
    if os.environ.get("OPENAI_API_KEY"):
        return AiChatStatus("openai", True, "OPENAI_API_KEY detected")
    if os.environ.get("ANTHROPIC_API_KEY"):
        return AiChatStatus("anthropic", True, "ANTHROPIC_API_KEY detected (bridge pending)")
    return AiChatStatus("nayak-local", False, "Rule-based NAYAK — set OPENAI_API_KEY for LLM")


def _local_reply(message: str, assistant: NayakAssistant, runtime: ApplicationRuntime) -> str:
    text = message.lower()
    permissions = AiPermissions()
    if any(word in text for word in ("live", "order", "broker", "buy", "sell")):
        return (
            f"{assistant.tk_name}, I cannot place or authorize live orders. "
            f"REQUEST_LIVE_ORDER is denied by policy. Live trading: "
            f"{runtime.status.live_trading}."
        )
    if "sharpe" in text:
        return (
            "Sharpe ratio is return per unit of risk. Above 1.0 is often interesting on real data. "
            "On synthetic drift in this lab, lower values are normal — not proof of NIFTY alpha."
        )
    if "momentum" in text:
        return (
            "Momentum tests whether recent winners keep winning on the next bar. "
            "Use the Test wizard — I enforce point-in-time fills so you cannot peek ahead."
        )
    if "validate" in text or "validation" in text:
        return (
            "Validation runs walk-forward and robustness checks. "
            "A single backtest can overfit — validation is the next discipline "
            "after your first run."
        )
    if "nifty" in text or "nse" in text:
        return (
            "This build uses synthetic NSE-style data. Real NIFTY feeds and F&O come later "
            "with extra risk controls. Learn safely here first."
        )
    if "help" in text or "what" in text:
        focus = assistant.focus()
        return f"I suggest: {focus.title}. {focus.body}"
    caps = ", ".join(c.value for c in sorted(permissions.granted, key=str))
    return (
        f"I'm NAYAK, your research assistant. I can discuss hypotheses, metrics, and workflow. "
        f"Granted capabilities: {caps}. "
        "Try asking about Sharpe, momentum, or validation."
    )


def _openai_reply(message: str, assistant: NayakAssistant, runtime: ApplicationRuntime) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return _local_reply(message, assistant, runtime)
    system = (
        f"You are NAYAK, a quantitative research assistant for {assistant.tk_name}. "
        "Research mode only. Never authorize live orders or promise profits. "
        "Be concise, calm, and honest about synthetic data limits."
    )
    payload = json.dumps(
        {
            "model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": message},
            ],
            "max_tokens": 400,
            "temperature": 0.3,
        }
    ).encode()
    request = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = json.loads(response.read().decode())
        content = body["choices"][0]["message"]["content"]
        return str(content).strip()
    except (urllib.error.URLError, KeyError, json.JSONDecodeError, TimeoutError) as exc:
        fallback = _local_reply(message, assistant, runtime)
        return f"OpenAI request failed ({exc}). Falling back: {fallback}"


def chat(runtime: ApplicationRuntime, message: str) -> str:
    assistant = NayakAssistant(runtime)
    cleaned = message.strip()
    if not cleaned:
        return "Ask me about Sharpe, momentum, validation, or what to do next."
    if os.environ.get("OPENAI_API_KEY"):
        return _openai_reply(cleaned, assistant, runtime)
    return _local_reply(cleaned, assistant, runtime)


def allows(capability: AiCapability) -> bool:
    return AiPermissions().allows(capability)
