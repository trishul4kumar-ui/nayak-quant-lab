# ADR-016 — Desktop framework: PySide6

## Context
Prompt 03 requires QUANT LAB to launch as a standalone desktop application. The quantitative core is Python (`src/quantlab`). Options were PySide6/Qt, PyQt, or Tauri/Electron.

## Problem
The UI must not own research, risk, or execution logic. The user must not need a browser, Cursor, or a cloud host to use the lab.

## Options
1. **PySide6 (Qt)** — native widgets, docking, threads, LGPL, first-class Python.
2. PyQt — same widgets, GPL/commercial licensing friction for a private lab.
3. Tauri/Electron — web frontend + extra runtime; core would still be Python via IPC.

## Decision
**Option 1. PySide6.** Application services live in `quantlab.app` with **no Qt imports**. `quantlab.ui` is a client of that layer.

## Consequences
- `python -m quantlab.ui` / `quantlab desktop` opens a native window.
- Tests for jobs, health, and commands run without a display.
- Packaging target is PyInstaller (ADR in `docs/development/PACKAGING.md`).
- Live trading remains impossible unless `LiveSafetyGates` all pass; the UI cannot call a broker.

## References
`docs/architecture/QUANT_LAB_DESKTOP_ARCHITECTURE.md`
