# Phase 44 — deterministic Trade Level Engine

Phase 44 follows the accepted Phase 43 adjudication gate: GitHub Actions CI
run [37609867338](https://github.com/trishul4kumar-ui/nayak-quant-lab/actions/runs/37609867338)
passed on 2026-10-07 for release-gate commit `99e506d`.

## Implemented boundary

- `quantlab.trade_levels` provides sealed input, policy, exit-policy, plan,
  freshness and chart-overlay contracts.
- The pure engine produces reproducible tick-rounded plans from frozen inputs.
  It does not call an LLM, provider, network, broker, portfolio, risk override
  or execution module.
- `TradeLevelRepository` persists only through the existing hash-addressed
  agent control plane and verifies upstream adjudication before calculation.
- The `trade-levels` CLI provides compute, inspect and history commands.
- The AI Quant Desk Levels tab displays only persisted plans, raw lineage,
  level-overlay values, exit policy and freshness. It has no calculate,
  approve, stage or order action.

## Failure behaviour covered

- identical frozen input/policy yields identical plan and exit-policy hashes;
- unknown volatility, invalid price, mismatched adjusted/raw basis, malformed
  quote, stale input and direction/adjudication mismatch fail closed;
- long/short arithmetic and tick rounding are directional and deterministic;
- `NO_VALID_ENTRY` creates no actionable price levels;
- an external market move marks a separate `STALE_LEVEL_PLAN` result rather
  than modifying the original plan;
- extra `quantity` and `order_type` fields are rejected by immutable contracts.

## Current limitation

The existing Phase 43 desk correctly returns `NO_TRADE` when complete canonical
market/risk/TCA evidence is unavailable. Therefore this phase does not invent a
candidate from current data. The engine and inspector are ready for a future
verified candidate, but a live candidate, sizing, paper order, broker write or
profitability claim is not produced here.

## Local verification

- `pytest -q tests/trade_levels/test_engine.py tests/agents/test_adjudication.py tests/ui/test_smoke.py`
  passed: 38 tests.
- Ruff and strict mypy are run again before phase publication.

Cloud acceptance is recorded only after the Phase 44 commit's pull-request or
main-branch CI run passes. Phase 45 remains pending that evidence.
