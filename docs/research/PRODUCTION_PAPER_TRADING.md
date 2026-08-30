# Production Paper Trading

**Version:** 2.4.0

Production-like paper trading runs the existing decision stack against current or research data and keeps books on Prompt 18 `PaperAccount`.

`quantlab shadow run --mode paper` without eligible certification does not silently become production. The cycle is recorded as `RESEARCH_PAPER` with `production_run=false` and a certification incident. `--mode paper` with `require_certified` fails closed.

Paper P&L is a paper result, not validated alpha and not a broker observation.
