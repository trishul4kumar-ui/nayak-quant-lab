# UI layer coordination (multi-agent)

**Updated:** 2026-08-30

Two agents may work on NAYAK QUANT LAB concurrently. Boundaries:

| Agent focus | Owns | Must not change without coordination |
|---|---|---|
| **Platform / quant** | `quantlab/core`, `domain`, `data`, `research`, `backtest`, `risk`, `portfolio`, `features`, `alpha`, `regimes`, `adaptive`, `learning` engines, `quantlab.app.worker`, `queries` data sources | `quantlab/ui/*` layout contracts |
| **UX / shell** | `quantlab/ui/*`, `quantlab/app/assistant.py`, `quantlab/app/settings_store.py` (UI prefs fields), UI tests | Quant engine logic, safety gates, ledger schema |

## Integration rules

1. UI calls **`quantlab.app`** only (bootstrap, jobs, queries, assistant) — never imports engine internals for side effects.
2. New desktop pages register in `quantlab/ui/navigation.py` + `main_window.py` page map.
3. Default nav key is **`home`** (Guided Lab). Full Lab exposes all engine pages.
4. UX spec: `docs/superpowers/specs/2026-08-30-nayak-quant-lab-ux-design.md`

## Phase 1 UX deliverables (this agent)

- `NayakAssistant` — TK greeting, focus suggestions, milestones
- `HomePage` — Jarvis-style home
- Guided / Full toggle + simplified nav
- Theme tokens (calm shell palette)
