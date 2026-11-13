# Real-only production data

Implemented locally on 15 October 2026. This is a data-source change, not permission
to trade. LIVE_TRADING and BROKER_WRITE_ENABLED remain false.

## Usable connected paths

- Market and Real-Time Data: the configured Kite GET-only quote source. Default
  gateway selection is Kite, not Mock. An empty/error response never loads seed
  observations or substitutes an earlier quote as a fresh observation.
- Charts and Backtest Lab: Kite historical candles, configured NSE/BSE instruments,
  explicit interval/range, closed bars only, frozen source/results and simulated
  next-bar-open fills for the displayed SMA baseline. No production synthetic option.
- NAYAK Operate Lab: real-data action grammar, matching host admission and a
  **Prepare real-data test** button. Plans still require human review and Run.
  Previously frozen synthetic plans cannot be dispatched in production.
- Data Fabric: select instrument/interval/calendar days, then **Capture real broker
  history**. This background GET-only job stores a frozen history and adds a REAL
  catalog entry without running a strategy. Backtests also catalog their history.
- Broker Gateway: Kite read-only account snapshots, not demo accounts. Portfolio
  Lab shows quantities/costs from an explicitly captured genuine Kite snapshot,
  with its timestamp. No fabricated weights, starting capital or PnL are substituted.

Restart using `scripts/QuantLab.command`. Credentials/watchlist stay in the existing
local Kite configuration; they are not copied into model prompts or artifacts.
Authentication, subscription, insufficient history and invalid-data errors stop the
operation. A working live quote connection alone does not prove historical API access.

## Advanced research: explicit real datasets, not silently relabelled candles

The shared research-frame loader and feature/factor/state/adaptive/model/ensemble
bar readers now select a version-pinned REAL dataset rather than auto-materializing
the memory seed. Selection uses `QUANT_LAB_RESEARCH_DATASET=dataset@version` in the
existing configuration. It must reference an eligible dataset in that workflow's
fabric root, with REAL labels, a research-ready PIT store, explicit historical
availability verification metadata, an intact raw-source checksum and matching
source/PIT price and availability facts. Missing, unverified or changed inputs fail.
This checks the supplied contract; metadata alone is not an independent certification.

Fresh Kite captures intentionally remain **NOT_READY** for that stronger PIT
contract: historic availability/revisions, corporate actions and historical universe
membership are not established by downloading candles today. Do not mark them
verified merely to bypass a blocked workflow. The broker-history SMA baseline is
separate exploratory research, not the old cross-sectional strategy with renamed data.
The guided cross-sectional wizard cannot silently substitute that SMA strategy.

The old econometric recipe manufactures AR/random-walk/cointegrated/panel series;
it is blocked until real series and an explicit analysis protocol are supplied.
Paper/shadow/monitoring/TCA/capital recipes cannot manufacture prices, liquidity,
covariance, expected returns, account cash or approved decisions. Their seeded entry
paths stop with REAL_DATA_REQUIRED. Real prices alone do not supply those inputs.
Seed passing-release evidence and fabricated aligned broker books are also blocked.
Missing requirements are displayed inline, not treated as a successful calculation.

## Retention and test boundary

Existing research ledgers and historical artifacts are retained under their original
labels. Archives are not current market evidence; they cannot drive new production
research/agent contexts as synthetic inputs. No old record is relabelled REAL and
no user research files are deleted.

Synthetic generators, corrupted scenarios and mock transports remain available only
to isolated software tests. `tests/conftest.py` sets a private fixture flag inherited
by spawned test workers. The production Mac launcher and the native acceptance
script clear it. Application widgets alone are not the boundary: input generators,
fabric admission, research integrity, agent contexts/plans and broker/feed defaults
enforce it as well. Simulated fills and statistical resampling of real returns are
not fabricated market prices and must never be labelled broker executions.

All tests using simulated transports are software contract evidence, not real market
or financial-validation evidence. Fresh connected acceptance must be reported
separately, including authentication/data failures, without a demo fallback.

## Verification and current connected blocker

The full offscreen regression suite passed **1,855 tests**; Ruff, strict Mypy
(913 source files), dependency consistency, whitespace checks and the wheel build
also passed. Focused production tests disable the fixture permission and exercise
real-source defaults, capture, host planning, generator refusals, version/checksum
binding, source tampering and missing-input behavior using simulated transports.
After adding the visible authentication diagnosis, the focused production/operator/
policy regression passed **58 tests**, including explicit no-fallback login failure.

The separate native Cocoa attempt with the actual configured local Qwen model
produced the correct BSE:BEL / REAL / five-minute / five-day market-backtest plan.
The GET-only broker request then failed with **Kite chart authentication rejected;
renew Kite login**. No result, simulated trade or synthetic fallback was fabricated.
This is a verified authentication blocker, not a successful fresh market-data run.
NAYAK displays a renewal diagnosis alongside the failed-job code.

Renew locally with `.venv/bin/python -m quantlab.cli market-data kite-login`,
complete the broker's login yourself, then reconnect in Market Lab and retry. Do not
paste tokens or passwords into chat. No credential, permission or safety setting
was changed to bypass this failure. All changes remain local; no commit/push.
