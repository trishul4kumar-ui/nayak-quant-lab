# NAYAK QUANT LAB — UX Design Specification

**Date:** 2026-08-30  
**Author:** TK (solo user) + design session  
**Status:** Approved direction — ready for implementation planning  
**Scope:** Desktop UI/UX (PySide6), single-user, beginner-to-power progression

---

## 1. Vision

NAYAK QUANT LAB is **TK's private quantitative trading laboratory** — not a generic tool, not a cloud product. It behaves like a **Jarvis-style assistant**: calm, personal, proactive, and always honest about what it knows and what it cannot do (especially live trading).

> *"Good evening, TK. Your lab is ready. Synthetic data is loaded — shall we run your next experiment?"*

The visual language blends three moods:

| Mood | Where it lives | Reference |
|---|---|---|
| **Calm teacher** | Home, onboarding, Learn, empty states | Soft spacing, one clear action, plain language |
| **Professional terminal** | Market, Backtest, charts, watchlists | Multi-panel mosaic, dark dense data (see user reference images: IB TWS, TradingView, multi-monitor setups) |
| **Personal lab notebook** | Journal, experiment cards, TK's notes | Warm accent, timeline, narrative over tables |

---

## 2. Design principles

1. **TK-first** — Greet by name; assistant speaks to TK, not "the user."
2. **Honest assistant** — NAYAK never implies live profits, hides synthetic nature, or bypasses safety gates.
3. **Progressive disclosure** — Guided Lab by default; Full Lab on toggle; milestones suggest, never block.
4. **Interactive terminal** — Panels are clickable, expandable, explainable — not static screenshots of Bloomberg.
5. **Correctness over chrome** — Visual polish serves understanding, not decoration.
6. **Indian market context** — Copy references NSE, NIFTY, ₹, IST (Asia/Kolkata); derivatives framed as a later learning path.

---

## 3. NAYAK assistant persona ("Jarvis layer")

### 3.1 What NAYAK is

- **Voice:** First-person lab assistant — *"I've loaded your data"*, *"I noticed you haven't validated yet"*
- **Name:** NAYAK (the lab itself speaks; the window title remains **NAYAK QUANT LAB**)
- **Tone:** Calm, precise, encouraging — never hype, never casino energy
- **Not:** A chatbot that places orders, overrides risk, or pretends to predict the market

### 3.2 Assistant surfaces

| Surface | Behavior |
|---|---|
| **Home greeting** | Time-aware: *"Good morning, TK"* / *"Good evening, TK"* + one-line lab status |
| **Focus card** | NAYAK suggests the single best next action with plain-language why |
| **Context strip** | Short proactive notes: *"3 experiments this week — want to compare them?"* |
| **Explain chips (? )** | On any metric/chart header — NAYAK explains in 2–3 sentences |
| **Full chat (future)** | AI Research page — subordinate to gates; not in Phase 1 |

### 3.3 Example copy

```
Good evening, TK.

Your lab is in RESEARCH mode. Live trading is off — as it should be while we learn.

Today's focus: Run a momentum backtest on synthetic NSE-style data.
I'll walk you through what Sharpe means when we're done.

[ Start experiment → ]
```

---

## 4. Experience modes (A + D hybrid)

### 4.1 Manual toggle

Header control: **`Guided Lab`** ◉ ─── ○ **`Full Lab`**

- Persisted in `ui.json` as `experience_mode: "guided" | "full"`
- Default: `guided` on first launch
- Full Lab reveals grouped power navigation immediately

### 4.2 Milestone memory

Persisted in `ui.json` as `milestones: string[]` and `visited_pages: string[]`.

| Milestone ID | Trigger | NAYAK suggests |
|---|---|---|
| `onboarding_complete` | Finish welcome | First backtest |
| `first_backtest` | Backtest job succeeds | Read Sharpe explanation |
| `first_equity_view` | Open equity chart | Try Validation |
| `first_validation` | Validation completes | Explore Features |
| `five_journal_entries` | 5 notes saved | Consider Full Lab |
| `full_lab_unlocked` | User toggles Full | — |

Milestones **suggest** only — TK can always toggle Full Lab or jump ahead.

---

## 5. Information architecture

### 5.1 Guided Lab navigation (5 items)

```
Home          → Greeting, focus, journal, pulse
Learn         → Glossary + mini-lessons tied to journey
Test          → 3-step backtest wizard
Journal       → Experiment timeline + TK notes
Settings      → Theme, mode, paths, milestones
```

Footer link: **Open Full Lab →**

### 5.2 Full Lab navigation (grouped)

```
Discover      Market · Data · Features
Research      Research · Alpha Lab · Models
Validate      Backtests · Validation
Build         Portfolio · Risk · Adaptive
Operate       Execution · Broker        (blocked / honest placeholders)
Reflect       Experiments · Journal · Logs · System
```

### 5.3 Home screen layout (approved blend)

```
┌──────────────────────────────────────────────────────────────────┐
│ NAYAK QUANT LAB     Good evening, TK.          [Guided ◉ Full]  │
├──────────────────────────────────────────────────────────────────┤
│ ┌─ NAYAK SAYS ────────────────────────────────────────────────┐ │
│ │ Today's focus · Step 2 of 5                                  │ │
│ │ Run your first momentum backtest on synthetic data           │ │
│ │                                    [ Start experiment → ]    │ │
│ └──────────────────────────────────────────────────────────────┘ │
│ ┌─ LAB JOURNAL ──────────────┐  ┌─ PULSE ─────────────────────┐ │
│ │ Today · Synthetic run       │  │ DATA     ✓ Ready            │ │
│ │ Sharpe 0.42 · synthetic     │  │ SYSTEM   ✓ Healthy          │ │
│ │ [+ Add note]                │  │ MODE     RESEARCH           │ │
│ │ Yesterday · Tour complete ✓ │  │ LIVE     DISABLED           │ │
│ └─────────────────────────────┘  │ LAST RUN 12 min ago         │ │
│                                   └─────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

---

## 6. Terminal visual system (from reference images)

User references: multi-monitor trading walls, Interactive Brokers TWS mosaic, TradingView 2×2 chart grids, watchlists with green/red heat.

### 6.1 Design translation (not a pixel clone)

We adopt the **structure and energy**, not proprietary layouts:

| Reference pattern | NAYAK implementation |
|---|---|
| 2×2 chart grid | `TerminalWorkspace` widget — resizable panel grid on Market / Backtest results |
| Watchlist tables | Color-coded rows (green ↑ / red ↓); click row → detail panel |
| Order book / depth | Deferred — placeholder with Learn link for derivatives path |
| Mosaic tabs | Bottom tab bar: *Overview · Charts · Tables · Notes* per page |
| Dark charcoal bg | `#0c0d10` workspace, `#1e222d` panels (TradingView-adjacent) |
| Neon data accents | `#26a69a` up, `#ef5350` down, `#42a5f5` chart lines |
| Gauges / heatmaps | Dashboard pulse cards; regime page heat strip (future) |

### 6.2 Interactive behaviors (beyond static terminal)

Every terminal panel MUST support at least one of:

- **Click** → expand to full panel / drill-down
- **Hover** → NAYAK tooltip with plain-English explanation
- **? chip** → persistent explain drawer
- **Right-click** (future) → "Add to Journal" / "Explain this metric"

Guided mode adds a **soft frame** around active panel (blue glow like TradingView selection in refs) so TK knows where to look.

### 6.3 Calm vs dense by mode

| Mode | Terminal density |
|---|---|
| **Guided** | Max 2 panels visible; third collapsed; larger fonts; more padding |
| **Full** | Up to 2×2 grid; 13px data font; minimal padding |

Same data, different information density — not different features.

---

## 7. Color & typography tokens

### 7.1 Dark theme (default)

```css
/* Shell — calm teacher */
--bg-shell:        #1c1f26;
--bg-surface:      #252932;
--text-primary:    #e8eaed;
--text-muted:      #9aa0a8;
--accent-calm:     #6ba3b8;

/* Terminal workspace */
--bg-terminal:     #0c0d10;
--bg-panel:        #1e222d;
--border-panel:    #2a2e39;
--chart-up:        #26a69a;
--chart-down:      #ef5350;
--chart-line:      #42a5f5;
--select-glow:     #2962ff;

/* Journal — warm notebook */
--bg-journal:      #2a2620;
--journal-accent:  #c9a96e;
--journal-paper:   #f0ebe3;

/* Safety */
--live-danger:     #9b3b3b;
```

### 7.2 Light theme (Phase 4)

```css
--bg-shell:        #f7f5f2;
--bg-terminal:     #ffffff;
--text-primary:    #2c2825;
```

### 7.3 Typography

| Use | Font | Size |
|---|---|---|
| UI body | System sans (SF Pro on macOS) | 14px |
| TK greeting | System sans, weight 500 | 22px |
| NAYAK voice | System sans, italic optional | 15px |
| Data / tables | Monospace (SF Mono / Menlo) | 13px |
| Panel headers | System sans, weight 600 | 12px uppercase tracking |

---

## 8. Key screens

### 8.1 Welcome (replaces bare splash)

1. NAYAK introduces itself to TK  
2. Confirms: research-only, no live trading  
3. Choose Guided (default) or Full  
4. Optional 60-second tour highlights: Home, Test, Journal  

### 8.2 Home

- TK greeting (time-aware, IST)
- NAYAK focus card (one CTA)
- Journal timeline (last 7 days)
- Pulse strip (system/data/mode/live)
- Milestone progress dots (subtle, not gamified)

### 8.3 Test wizard (Guided)

| Step | NAYAK says | UI |
|---|---|---|
| 1 — What | *"Let's test if recent winners keep winning — a classic momentum idea on synthetic NSE names."* | Strategy card, no jargon without ? |
| 2 — Run | *"Running now. This uses next-bar fills — no peeking at the future."* | Progress bar, cancel |
| 3 — Result | *"Here's what happened. On synthetic data, this Sharpe is expected — not proof of real alpha."* | Equity chart panel + metrics + [Save to Journal] |

### 8.4 Terminal workspace (Market / Backtest results / Full Lab)

- `QSplitter` / grid of `TerminalPanel` widgets
- Each panel: title, ? chip, content, expand button
- Watchlist panel: sortable, color-coded
- Chart panel: reuse `EquityCurveWidget`, extend for candlesticks later

### 8.5 Journal

- Cards, not raw `QTableWidget` as primary view
- Each card: date, experiment name, key metric, TK note (editable), [Open in Full Lab]
- Warm `--bg-journal` background zone

### 8.6 Learn

- Concepts grouped by journey stage, not A–Z
- Sections: *Starting out · Backtesting · Validation · Portfolio · Risk · Derivatives (coming)*
- Indian context: NIFTY, F&O basics as later modules

---

## 9. Technical mapping (existing codebase)

| New concept | Location | Notes |
|---|---|---|
| Experience mode + milestones | `quantlab.app.settings_store.UiSettings` | Extend model |
| NAYAK copy / focus logic | `quantlab.app.assistant` (new) | Rule-based; no LLM required Phase 1 |
| Home redesign | `quantlab.ui.pages.home` (new, replaces dashboard as default) | Dashboard logic reused in pulse |
| Terminal panels | `quantlab.ui.widgets.terminal` (new) | Panel, Grid, Watchlist |
| Theme tokens | `quantlab.ui.theme` | Replace monolithic STYLESHEET with tokens |
| Guided nav | `quantlab.ui.main_window` | Filter `NAV` by mode |
| Journal notes | `ui.json` or sqlite `journal_notes` | Start with ui.json |
| Explain chips | `quantlab.ui.widgets.explain` (new) | Static copy map Phase 1 |

**Unchanged:** `quantlab.app` job pipeline, safety gates, ledger, all quant engines.

---

## 10. Implementation phases

### Phase 1 — Foundation (ship first)

- [x] Extend `UiSettings` (`experience_mode`, `milestones`, `visited_pages`, `theme`, `tk_display_name`)
- [x] New theme tokens (shell + terminal palettes)
- [x] `NayakAssistant` service (greeting, focus suggestion, milestone checks)
- [x] New `HomePage` with TK greeting + focus + journal stub + pulse
- [x] Guided / Full toggle in header
- [x] Guided nav (5 items) vs Full nav (grouped)

### Phase 2 — Terminal interactivity

- [x] `TerminalPanel` + `TerminalGrid` widgets
- [x] Refactor Backtest results into 2-panel layout (chart + metrics)
- [x] Refactor Market page into watchlist + detail split
- [x] Explain chips on all metrics
- [x] Milestone tracking wired to job completion

### Phase 3 — Journal & Learn

- [x] Journal page with editable TK notes
- [x] Learn page with staged glossary
- [x] Test wizard (3-step) replacing direct backtest jump in Guided mode
- [x] Welcome flow replacing bare splash

### Phase 4 — Polish

- [x] Light theme
- [x] Panel drag-resize / saved layouts
- [x] NAYAK context strip (proactive suggestions)
- [x] AI Research chat integration (when AI keys present)

---

## 11. Success criteria

TK opens the app and feels:

1. **Recognized** — greeted by name, lab feels personal  
2. **Guided** — knows exactly one thing to do next  
3. **Empowered** — terminal views feel professional, not toy-like  
4. **Safe** — live trading clearly off; synthetic data clearly labeled  
5. **Growing** — Full Lab available when ready; journal shows progress over weeks  

---

## 12. Out of scope (this spec)

- Live broker connection UI beyond honest placeholders  
- Real NSE tick feed / order book  
- Full candlestick charting library (use equity curve first)  
- LLM-powered NAYAK chat (Phase 4 optional)  
- Multi-monitor spanning (single window first; internal grid simulates wall)

---

## 13. Reference images (user provided)

Stored in project assets — multi-monitor trading setups, IB TWS mosaic, TradingView dark grid. Used as **density and layout inspiration**, not assets to reproduce verbatim.

---

*Next step: implementation plan for Phase 1.*
