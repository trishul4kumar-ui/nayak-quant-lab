# Phase 39 — Agent foundation

Implemented immutable/versioned contracts, a shared authoritative capability policy,
typed snapshot-bound tool gateway, canonical feature-engine adapter, durable SQLite
artifact/audit repositories, trust-separated prompt sections, provider-neutral
interface, OpenAI Responses structured-output adapter, schema/deadline/cancellation
handling, and optional display-only Qt bridge with native fallback.

CLI: `agents status`, `permissions`, `tools`, `audit`, `provider-health`.
Desktop: Full Lab → AI Quant Desk. It displays native analyst state/history,
permissions, real binding status and audit without pretending agents have run.

The provider requires `OPENAI_API_KEY` and an explicit `QUANT_LAB_AGENT_MODEL`.
Presence of credentials is CONFIGURED/NOT_TESTED, never verified connectivity.
No remote model request or credential change was made during implementation.

Phase 39 is release-accepted for `3abef8f`: all required cloud gates passed in
[CI run 37175625914](https://github.com/trishul4kumar-ui/nayak-quant-lab/actions/runs/37175625914).
Publication and the portability/test/workflow fixes are recorded in
BUILD_PROGRAM_39_53.md. No production or profitability claim is made.

## Included improvements

- Fixed hidden sidebar-search focus in compact layouts and duplicate terminal-panel
  focus callbacks after responsive reflows. These caused actual no-reaction clicks.
- Persistence failures are redacted and fail closed; a corrupt desk database does
  not crash the rest of the application or get overwritten. Stale inspector content
  is replaced with an explicit blocked state.
- Unknown/mixed provenance cannot become REAL data by default; historical frames
  must match snapshot scope, availability, data kind, and price basis.
- The optional WebEngine station surface has usable height, local-only asset access,
  isolated in-memory profile, deterministic disposal, and native navigation fallback.

## View the foundation

```sh
cd "/Users/vaibhavkumarn/Desktop/NAYAK QUANT LAB"
source .venv/bin/activate
QUANT_LAB_AGENT_VISUALS=1 python -m quantlab.ui.main
```

Choose **Full Lab → Research → AI Quant Desk**. Analyst states are IDLE until the
later phases implement workers; unavailable provider/analysis status is intentional.
Omit `QUANT_LAB_AGENT_VISUALS=1` for native-only inspectors. Model configuration is
not needed to view permissions, tools, audit, or the foundation page.

Official documentation checked at implementation time:

- [OpenAI structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
- [Qt WebChannel](https://doc.qt.io/qtforpython-6/PySide6/QtWebChannel/QWebChannel.html)
- [Qt WebEngine](https://doc.qt.io/qt-6/qtwebengine-overview.html)
- [Three.js installation](https://threejs.org/manual/#en/installation)
- [Kite streaming](https://kite.trade/docs/connect/v3/websocket/)

The OpenAI Docs skill informed schema-required fields and explicit refusal/incomplete
handling. It did not require deployment or transmission of the user's market/account data.
