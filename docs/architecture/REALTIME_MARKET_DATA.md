# Real-Time Market Data & State Gateway

**Version:** 3.1.0  
**Package:** `quantlab.realtime_data`  
**Desktop:** Real-Time Data Lab (`rt_data`)  
**CLI:** `quantlab realtime`

Observe-only production-time counterpart to the Prompt 20 fabric. Default adapter: `MockMarketDataAdapter`.
An optional `KiteMarketDataAdapter` uses Kite Connect v3's REST quote endpoint
only when local environment configuration supplies explicit exchange-scoped
symbols. It has no vendor order client or write transport.

```text
LIVE_TRADING=false
BROKER_WRITE_ENABLED=false
REAL-TIME OBSERVATION ≠ TRADING
CONNECTED ≠ HEALTHY
```

Frozen snapshots are immutable. Stale/invalid/missing never silently become valid. Vendor SDKs are not imported.

`/quote` is a point-in-time REST snapshot and does not provide a market-event
sequence. The adapter records that limitation as `sequence_guarantee=not_provided`;
it never invents sequence numbers or claims stream-level gap detection. A later
WebSocket adapter must provide its own explicit sequence/provenance semantics.

## Native live quote workspace

Market Lab now reads **Kite quotes**, not the synthetic `MemoryBarProvider`.
Click **Connect Kite** after daily authentication. Its shared desktop session
refreshes `GET /quote` every two seconds in a single background worker; the UI
remains responsive. Real-Time Data Lab uses that same session. No page issues
orders or silently substitutes demo prices when Kite fails.

```sh
cd "/Users/vaibhavkumarn/Desktop/NAYAK QUANT LAB"
source .venv/bin/activate
python -m quantlab.cli market-data kite-login
python -m quantlab.cli desktop --kite-quotes
```

The `--kite-quotes` option opens Market Lab and connects automatically. Without
that option, use **Research → Market → Connect Kite**. Explicit instruments come from local
`KITE_MARKET_DATA_SYMBOLS` (for example `NSE:INFY,NSE:TCS`). Keep `LIVE_TRADING=false`
and `BROKER_WRITE_ENABLED=false`. Never share or commit API secrets/tokens.

- LTP, bid/ask, volume, provider timestamp (IST), quote age and quality are shown.
  Missing fields/instruments display unavailable, not zero or demo values.
- Quote age is recomputed against the current clock using
  `KITE_MAX_QUOTE_AGE_SECONDS` (default five). A freshly received stale quote is
  still stale. Closed-market quotes are not advertised as live trading data.
- The **Observed quotes** chart contains only valid, fresh provider-timestamped quotes observed
  during this app session (at most 1,800 per instrument). Duplicate timestamps
  are not new samples; pauses/errors and long gaps are not interpolated. It is
  not historical candles, tick coverage, or a validated momentum/regime signal.
- **Pause feed** stops further requests and discards late results. Errors retain
  last-known prices marked unavailable; network errors back off up to 60 seconds.
  Authentication rejection stops polling. Renew with `kite-login`, then reconnect;
  credentials are re-read per request without restarting the desktop.
- Polling is ephemeral. **Capture Kite snapshot** explicitly retains a frozen
  snapshot for existing downstream inspection; automatic refresh does not grow
  the snapshot/audit stores. The separately labelled synthetic demo remains
  an explicit research action only.
- **KITE DATA** in the footer describes the quote session; **BROKER** describes
  the separate broker account session. Neither authorizes execution. The calendar
  remains `weekday-v1`, not a verified exchange holiday calendar.

### Expanded local watchlist (7 October 2026)

The local watchlist contains 46 distinct exchange-scoped instruments: the existing
INFY/TCS pair plus all 44 instruments visible in the supplied stock/index screenshots.
Their identities were checked against Kite's `GET /instruments` CSV; a single
`GET /quote` request returned all 46 keys. This verifies quote availability at the
time of the check, not continuous freshness, tradability or execution permission.

| Group | Configured instruments |
| --- | --- |
| Existing | `NSE:INFY`, `NSE:TCS` |
| Watchlist 2, visible rows | `NSE:BEL`, `BSE:BEL`, `NSE:HAL`, `BSE:HAL`, `NSE:TATASTEEL`, `BSE:TATASTEEL`, `NSE:NIFTYBEES`, `BSE:NIFTYBEES`, `NSE:IRCON`, `BSE:IRCON`, `BSE:RVNL`, `NSE:RVNL`, `NSE:ONGC`, `BSE:ONGC` |
| Watchlist 3 | `BSE:UCOBANK`, `NSE:UCOBANK`, `NSE:RAJMET`, `BSE:YESBANK` |
| Indian indices, visible rows | `NSE:NIFTY 50`, `NSE:NIFTY NEXT 50`, `NSE:NIFTY 100`, `NSE:NIFTY 200`, `NSE:NIFTY MIDCAP 150`, `NSE:NIFTY SMLCAP 250`, `NSE:NIFTY BANK`, `NSE:NIFTY IT`, `NSE:NIFTY AUTO`, `NSE:NIFTY PHARMA`, `NSE:NIFTY FMCG`, `NSE:NIFTY REALTY`, `BSE:SENSEX`, `BSE:BANKEX` |
| Global indices / yield | `GLOBAL:USCOMPOSITE`, `GLOBAL:US30`, `GLOBAL:US100`, `GLOBAL:US500`, `GLOBAL:SHANGHAICHINA`, `GLOBAL:UK100`, `GLOBAL:HANGSENG`, `GLOBAL:AUS200`, `GLOBAL:FRANCE40`, `GLOBAL:GERMANY40`, `GLOBAL:JAPAN225`, `GLOBAL:US10YRYIELD` |

`KITE_MARKET_DATA_SYMBOLS` in the ignored local `.env` holds these comma-separated
identities. The running desktop re-reads them on each poll; **Refresh quotes** or
**Connect Kite** uses the updated list. Preserve spaces in index symbols when
editing `.env`; if assigning this list in a shell, quote the entire value.
This changes the Quant Lab watchlist, not the watchlists saved on Kite's website.

Values are displayed in provider-native units, not universally labelled rupees.
Absent index depth/volume stays unavailable. Older global quotes remain stale,
and the aggregate feed can report **STALE** even while Indian instruments are
fresh; inspect each row's quote age/quality. The Indian weekday session flag is
not a global exchange-session or holiday calendar. No freshness threshold was
relaxed to make the expanded watchlist appear healthy.

The screenshots hide eight Watchlist 2 rows and ten Indian indices, and show only
collapsed MCX group headings. Those entries were **not guessed**: an expanded
screenshot or an exact exchange:symbol list (including futures expiries) is needed.
All requests remain GET-only with live trading and broker writes disabled.

## Interactive Market Lab charts

Selecting a watchlist instrument now drives a native chart workspace with real
Kite historical candles and a separately quality-labelled current quote marker.
The historical source is `kite-historical-v3`; observed quote samples remain
`kite-rest-quote-v3`. The candle loader resolves the exact configured instrument
token through `/quote`, then calls the GET-only historical endpoint. No chart
view, drawing or export can authorize an order.

- Views: **Candles**, **OHLC**, **Line**, **Area** and **Observed quotes**.
- Provider intervals: **1m, 3m, 5m, 10m, 15m, 30m, 1h, daily**. Ranges are Today,
  five calendar days, one month (31 days), and one year (366 days, daily only).
  The dropdown automatically switches to daily for the one-year range.
- Navigation: mouse wheel zooms around the cursor; drag pans; **Fit** shows the
  loaded range; **Latest** follows incoming updates. Keyboard `+`/`-`, `Home`,
  `End` and left/right arrows also work. Hover displays exact timestamp, OHLC
  and volume; incomplete candles are labelled **forming / may revise**.
- Display indicators: SMA 20, EMA 9 and 26, Bollinger Bands (20 closes, ±2
  population standard deviations), and Wilder RSI 14. Their warm-up periods
  remain empty, not zero. Volume uses a zero-baseline pane; absent and returned
  zero volume are distinguished. Indicator values are descriptive, not signals.
- **Horizontal** and two-click **Trend line** add local annotations. **Undo**
  and **Clear** affect drawings only. Drawings reset when the instrument,
  timeframe/range or candle origin changes; they are not persistent trade levels.
- **Expand** opens the entire workspace, including its controls and readouts;
  **Restore** or closing that window returns it to the original panel. The
  toolbar reflows into one column at narrow sizes. **PNG** saves the workspace;
  **CSV** exports loaded source data with UTC times, source and interval metadata.
- **Auto · 20s** refreshes candles in a bounded single background worker;
  current quotes use the separate two-second quote session. Uncheck Auto to
  keep the captured candles; **Reload** explicitly refreshes them. Pausing the
  quote feed stops new chart requests. Late selection results cannot overwrite
  another instrument. Authentication failures halt retries until Reload or
  another selection; renew the daily login first.
  In Observed quotes mode, candle-only controls are disabled and **Reload**
  refreshes the quote session instead. Undo/Clear are disabled without drawings.

Candles use a trading-bar axis with closed-session gaps compressed; their exact
IST timestamps remain available on hover. Observed quotes use an elapsed-time
axis and never bridge pauses or missing samples. Line/area views do not fill
across missing-session segments. Empty or failed history stays explicitly
unavailable; it is not replaced with fabricated candles. A real check on
7 October 2026 returned one-minute YESBANK and NIFTY 50 candles, but no US30
historical candles, despite US30 quote availability.

Kite's [historical API](https://kite.trade/docs/connect/v3/historical/) starts at
one-minute candles. The ten-second chart in the reference screenshot needs a
separate validated streaming/aggregation integration; REST quotes are not full
tick coverage. This implementation deliberately does not manufacture ten-second
OHLC from two-second polls. Daily candle completion is conservatively labelled
using its interval boundary, not a validated per-exchange holiday/session close.

Interactive chart source, loader, navigation, indicators, exports and source
separation are covered by Qt offscreen and deterministic adapter tests. Real
provider candles were also rendered at wide/narrow widths. These checks verify
software behavior, not investment performance or production trading readiness.
Test fixtures redirect default experiment and desktop storage into temporary
directories and release test-owned Qt windows between cases; validation does not
need the user's research stores or leave accumulated windows for theme checks.

### macOS automated inspection limitation

Native accessibility inspection on this machine (PySide6/Qt 6.11.2, macOS 26.5.2)
triggered `libqcocoa` / `NSAccessibility` segmentation faults. The stack matches
the reported [Qt/Codex computer-use issue](https://github.com/openai/codex/issues/41374).
That is not a Kite authentication or quote error. Live cells and footer chips
now update in place, but that does **not** establish an upstream Qt fix. Avoid
automated accessibility-tree inspection pending a verified toolkit fix; do not
disable accessibility or downgrade dependencies silently. Live quotes and controls
are additionally tested through Qt fixtures and source-backed rendered checks.
