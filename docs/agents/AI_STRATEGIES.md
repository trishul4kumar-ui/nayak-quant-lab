# Automatic AI strategy research (local, research-only)

Open **Backtest Lab → AI Strategy Lab ↗**, or the separate AI window's
**Develop & backtest strategies → AI Strategies** tab.

Choose your objective, configured instrument, interval, history range, candidate
count and time budget. **Develop strategies & run automatic batch** starts one
finite job. No approval is needed between candidates. The job presents its report
automatically when it finishes; cancelled/failed jobs are not labelled completed.
Opening the workspace does not make model calls or start jobs.

The default data source captures broker history once through the existing GET-only
Kite adapter. Alternatively select exactly one immutable frozen history version.
Daily history is limited to 366 calendar days; intraday history to 31. Only completed
bars are used. Quote connectivity does not imply historical API permission. Missing
credentials, insufficient history or an unavailable model stop the job; there is
no synthetic-price or hidden-model fallback.

This is historical backtesting, including recent completed intraday bars—not
streaming forward testing, a recurring scheduled run, or automatic live trading.

## What the AI can develop

The configured model proposes data-only long/cash strategy definitions. It can
combine trailing close/SMA and fast/slow SMA gaps, simple rolling RSI, trailing
returns, prior-channel breakouts, realized volatility and observed volume ratios.
Entry/exit conditions support comparisons and crossings, all/any combinations,
partial cash allocation, close-triggered stop/target decisions and time exits.
No generated Python, `eval`, shell commands, plugins or arbitrary indicators are
executed. New algorithms outside this DSL still require a reviewed implementation.

AI names and explanations are unverified model text. They can misdescribe a rule
(the local acceptance exposed this). The host generates a separate description
directly from the exact rules; that description and the frozen JSON govern the
test. Shorting, leverage and broker authority cannot be expressed in the schema.

Backtest Lab now offers six real-data presets: close/SMA, fast/slow SMA, RSI mean
reversion, prior-channel breakout, momentum, and volatility-filtered trend.
Saved AI proposals from completed batches also appear in the selector. The report's
**Open selected AI strategy in Backtest Lab** transfers the exact definition, not
an approximate preset. This does not start another run. Untraded/rejected proposals
remain proposals, never validated strategies.

## Automatic protocol and safeguards

- At most 8 AI candidates plus one fixed SMA comparison; at most 2 bounded model
  requests (one generation and one schema retry). Default: 4 candidates, 180 seconds,
  a maximum 3,000-bar analytical tail; hard limits: 600 seconds and 6,000 bars.
- After a common causal warm-up, eligible bars split chronologically 60%/20%/20%
  into training/validation/holdout. Minimum segment sizes are enforced. Only
  training summary statistics, source metadata, objective and assumed costs reach
  the model. Validation and holdout prices/results are not supplied to it.
- All candidates run training and validation automatically. The predeclared score
  is validation excess return over buy/hold minus half the absolute validation
  drawdown. A candidate must have simulated fills in both segments to be eligible.
  Duplicate rule sets are rejected even when renamed. Every outcome is retained.
- The proposed family, parameters, source history and split boundaries are sealed
  in the existing hash-addressed artifact store before the first candidate test.
  On reopening a new-format report, the loader checks the family, candidate audit
  sequence, validation scores and frozen winner. This is an internal freeze after
  the model saw the training summary, not external preregistration or evidence that
  all related experiments are known. Old reports without family artifacts remain
  legacy exploratory records.
- The best eligible **AI** candidate is selected by that score; the SMA baseline
  remains a comparison, not an AI-authored candidate. Selection is frozen and
  audited **before** the only winner holdout calculation. Best-of-batch does not
  imply positive return, superiority to the baseline, statistical significance,
  or permission to trade. No eligible candidate means abstention.
- Segments start with a fresh normalized 100,000-unit account and no position;
  feature warm-up may use preceding observations. These units are not broker cash.
  Signals use completed bars and fill at the next available open. Stops/targets
  are prior-close-triggered, not intrabar stops. Costs/slippage are explicit;
  taxes, calibrated impact and execution/liquidity guarantees are absent. Open
  positions are marked at the final close, not force-liquidated.
- Training/validation days are recorded before model generation, and holdout days
  are reserved before the holdout calculation. A single SQLite write transaction
  makes the prior-record check and reservation atomic, including across processes.
  Failed, cancelled, partially published, or interrupted attempts therefore leave
  conservative exposure records; a reserved-but-never-read period may be marked
  as used. Overlap uses the same instrument and exchange-local calendar days,
  including different bar intervals and new history captures. A later holdout
  overlapping any previously recorded research or holdout range is permanently
  labelled `HOLDOUT_REUSED`. The report loader verifies its exposure record,
  prior audit sequence, reuse flag and warning. Missing or corrupt ledger evidence
  fails closed. Saved reports are checked against the entire bound frozen history,
  including training, validation and warm-up, so their saved history can be
  conservatively overclassified as exposed. Missing or invalid bound history
  blocks the check. Unrecorded failed attempts before the ledger was introduced
  cannot be reconstructed. Repeated research is not untouched out-of-sample evidence.
- The exposure ledger covers only this strategy workflow and this local store.
  Other backtests, notebooks, screenshots, external experiments, aliases and
  related instruments can expose the same information without being tracked.
  Its source/audit hashes detect accidental corruption, not an adversary with
  write access to both tables. The legacy-overlap bit is captured from a scan of
  earlier reports, not independently authenticated. No claim of a globally
  untouched holdout or independent validation follows from a clear local check.
- Cancellation is cooperative during I/O/calculation and prevents final report
  publication when accepted. Once publication begins, cancellation is refused.
  A time-budget exhaustion can publish a clearly labelled partial report, never
  claim that uncomputed candidates ran. Partial proposal/selection audit records
  may remain, but are excluded from completed reports and the saved-strategy list.

Reports bind exact history, definitions, model identity, selection, parameters and
host results with verified hashes. They include all attempts, costs, normalized
equity and buy/hold series, assumptions, and full-value inspect/copy/export.
The UI auto-selects only the owned completed batch; it does not silently substitute
an unrelated result. Persisted reports can be reopened without another model call.

`COMPLETED` means software finished. REAL prices do not establish point-in-time
availability, corporate-action correctness, calendar/constituent integrity, robust
alpha, or independent validation. All validation/promotion gates remain
**NOT_TESTED**; `LIVE_TRADING=false`, `BROKER_WRITE_ENABLED=false`.

## Reproduce isolated actual-source acceptance

With the existing broker/model configuration available, run from the local repo:

```sh
strategy_test_dir=$(mktemp -d /tmp/nayak-strategy-acceptance.XXXXXX)
.venv/bin/python scripts/strategy_batch_acceptance.py --data-dir "$strategy_test_dir" --latest --instrument BSE:BEL --candidates 3 --render
```

The script uses the same widget-submitted background job, reads broker history
without order endpoints, and writes only to its isolated directory. It produces
`acceptance.json`, `strategy-report.json`, native screenshots and the frozen store.
Never use your normal application data directory as the acceptance destination.
`--source-store PATH` substitutes one explicitly sourced daily frozen capture;
`--rerun-isolated` is restricted to an existing marked acceptance directory and
allows the overlapping-holdout warning to be verified. Neither path commits,
pushes, configures a gateway, changes credentials or relaxes safety gates.

Automated tests use deterministic generated prices and an explicit test-double
model; they are software checks, not market performance evidence.
