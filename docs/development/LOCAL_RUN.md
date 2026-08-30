# Run QUANT LAB locally

Python 3.12+ and the project virtualenv.

```bash
cd "NAYAK QUANT LAB"
python3.12 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
make install
```

Copy `.env.example` to `.env`. Keep `LIVE_TRADING=false` and `QUANT_LAB_MODE=research`.

## Desktop application

```bash
make desktop
# or
quantlab desktop
# or
python -m quantlab.ui
```

On macOS you can also double-click `scripts/QuantLab.command` after `chmod +x`.

The window is native Qt (PySide6). You do not need Docker, a browser, or Cursor to use it.

Application data (ledger, logs, sqlite jobs, UI prefs) goes to the OS data directory, or to `QUANT_LAB_DATA_DIR` if set.

| Platform | Default data root |
|---|---|
| macOS | `~/Library/Application Support/QUANT LAB` |
| Windows | `%APPDATA%\QUANT LAB` |
| Linux | `~/.local/share/quantlab` |

Development tip: `QUANT_LAB_SKIP_SPLASH=1` skips the startup dialog. Tests use `QT_QPA_PLATFORM=offscreen`.

## CLI research slice (no UI)

```bash
quantlab slice
quantlab backtest run
quantlab validate run
quantlab feature list
quantlab research feature momentum_20
quantlab portfolio list
quantlab research portfolio mom20_topn
quantlab factor list
quantlab research factor style_momentum_20
quantlab risk list
quantlab risk compute sample_cs
quantlab state list
quantlab regime list
quantlab research regime vol_tercile
quantlab adaptive list
quantlab research adaptive static_mom20
quantlab model list
quantlab research model ols_mom
quantlab ensemble list
quantlab research meta-alpha
quantlab execution list
quantlab execution inspect exec_base
quantlab execution simulate exec_base
quantlab research execution
quantlab hypothesis list
quantlab experiment plan EXP-MOM-001
quantlab research discover
quantlab research status
quantlab discovery list
quantlab discovery inspect GP-MOM-VOL-001
quantlab discovery search
quantlab knowledge list
quantlab knowledge report H-MOM-001
quantlab capital list
quantlab capital inspect CAP-RESEARCH-001
quantlab capital allocate mom20_topn
quantlab paper list
quantlab paper submit last
quantlab monitor run
quantlab monitor attribution
quantlab tca run
quantlab tca shortfall
quantlab econometrics stationarity
quantlab econometrics granger
quantlab validation create
quantlab validation run
quantlab shadow health
quantlab shadow audit
quantlab shadow run --mode research_paper
quantlab shadow run --mode paper
quantlab shadow run --mode shadow
quantlab safety status
quantlab safety audit
quantlab ops doctor
quantlab ops health
quantlab certification status
quantlab certification audit
quantlab broker health
quantlab broker snapshot
quantlab realtime health
quantlab realtime snapshot
quantlab realtime-decision status
quantlab realtime-decision run
quantlab twin run
quantlab twin replay
quantlab twin determinism
quantlab data calendar
quantlab data universe
quantlab data list
quantlab data ingest synthetic
make test
```
