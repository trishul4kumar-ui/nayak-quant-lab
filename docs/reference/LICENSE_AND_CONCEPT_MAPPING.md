# License and concept mapping

QUANT LAB does not copy modules from reference repositories. Concepts below were studied from public source trees on 2026-08-30.

| Reference | License | Concept | Why useful | QUANT LAB | Difference | Risk |
|---|---|---|---|---|---|---|
| Qlib | MIT | Dataset + PIT + recorder | Research workflow | Dataset version, PIT, JSONL ledger | No global `init()`, no NFS | Do not copy `qlib/data` |
| OpenBB | AGPL-3.0 | Provider/consumer split | Vendor isolation | `MarketDataProvider` | Independent code; **no OpenBB source** | AGPL copy would infect this tree |
| VN.Py | MIT | Event engine + gateway | Trading OS | EventBus + BrokerGateway | No Qt UI | Keep MIT notices if we ever vendor a snippet (we do not) |
| Hummingbot | Apache-2.0 | Connector + paper + order states | Execution | PaperGateway, OMS states | Crypto-first unused | Apache notice if vendoring |
| StockSharp | Apache-2.0 | Rich instrument | Identity | InstrumentId + lot/tick | C# unused | — |
| OpenAlgo | see repo License.md | Indian broker façade | IN execution | Future adapter only | We own domain | Treat as untrusted network |
| QuantDinger | see repo | Workers, Postgres SoT | Ops | Deferred workers; Redis not SoT | — | Live opt-in |
| Lumibot | see repo | One strategy, many runtimes | Strategy protocol | Strategy protocol | — | — |
| TradingAgents | see repo | Role decomposition | Research agents later | Permissions + hypotheses | LLM not OMS | Non-reproducible LLM |

**Rule:** inspect license before adding a dependency. Prefer independent implementations.
