# QUANT LAB Desktop Architecture

**Status:** Prompt 18 (2026-08-30) — desktop remains a client; Features, Alpha Lab, Portfolio Lab, Risk Lab, Market Lab, Adaptive Lab, Model Lab, Ensemble Lab, Execution Lab, Capital Lab, Paper OMS Lab, Research Control, Discovery Lab, and Knowledge Lab query `quantlab.app`.  
**Does not replace** the quantitative target in `QUANT_LAB_TARGET_ARCHITECTURE_v0.2.md`.

## Principle

The desktop is a **client** of the research engine. Widgets never place orders, compute alphas, or authorize risk.

```
                 QUANT LAB DESKTOP (PySide6)
                        │
              ┌─────────┴─────────┐
              │                   │
          UI SHELL          quantlab.app
          (Qt only)         (no Qt)
              │                   │
              └─────────┬─────────┘
                        │
                  QUANT LAB CORE
                        │
       ┌────────────────┼────────────────┐
       ▼                ▼                ▼
   DATA FABRIC      QUANT CORE        RISK / OMS
```

## Process

```
Launch
  → bootstrap (paths, logging, sqlite, health)
  → splash / health
  → main window
  → user runs backtest as a Job (worker thread)
  → ledger + results
  → shutdown (cancel jobs, persist UI settings, flush logs)
```

## Packages

| Package | Qt? | Authority |
|---|---|---|
| `quantlab.app` | no | mode, paths, health, jobs, commands, UI settings file |
| `quantlab.ui` | yes | windows, navigation, charts, log viewer |
| existing core | no | data, math, research, risk, backtest, brokers |

## Operating modes

`DEVELOPMENT | RESEARCH | PAPER | SHADOW | LIVE`

Default **RESEARCH**. `LIVE` is refused unless every `LiveSafetyGates` flag passes. The UI confirmation dialog is extra, not a substitute for the firewall.

## Local state (OS application-data directory)

```
QUANT LAB data root
├── database/app.sqlite     jobs
├── research/ledger.jsonl   experiments (same contract as Prompt 01)
├── fabric/                 PIT layers (raw/normalized/curated/pit/…)
├── logs/quantlab.log
├── settings/ui.json        window geometry (no secrets)
└── artifacts/
```

Override with `QUANT_LAB_DATA_DIR` (tests and portable installs). Never hardcode user home paths in source.

DuckDB is the PIT query engine over Parquet. Postgres remains deferred. The UI never queries Parquet itself.

## Jobs

Long work (backtest) runs in a thread pool. The UI polls job status. Cancel sets a flag; workers must not be `kill -9`'d.

## Safety visible in the shell

- Mode badge always shown.
- `LIVE` is visually unmistakable and off by default.
- Broker disconnected / live ordering blocked is a first-class status, not a log line.
- Closing the window is not a portfolio flatten.

## What this stage does not include

Full docking research workspace, PyInstaller installer for end users, paper OMS UI, OpenAlgo, AI agents in the window.
