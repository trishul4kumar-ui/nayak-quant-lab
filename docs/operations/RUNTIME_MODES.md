# Runtime modes

`QUANT_LAB_MODE` selects the operating mode shown in the desktop shell.

| Mode | Meaning | Live orders |
|---|---|---|
| `development` | Local engineering | Blocked |
| `research` (default) | Experiments, backtests, ledger | Blocked |
| `paper` | Same strategy path, paper gateway | Blocked (paper fills only, later) |
| `shadow` | Signals vs market, no real orders | Blocked |
| `live` | Real broker | Only if **every** `LiveSafetyGates` flag is true **and** a live adapter exists |

`LIVE` requested without gates is coerced to **RESEARCH**. The desktop “Request live trading…” dialog cannot override the firewall. This build has no live broker path.

Closing the window is not a portfolio flatten. If live were active, positions could remain at the broker.

Visible status (from `quantlab.app.status.SystemStatus`, not hardcoded UI copy):

```
SYSTEM / DATA / RESEARCH / RISK / BROKER / LIVE TRADING
```

Broker disconnected and live ordering blocked are first-class states.
