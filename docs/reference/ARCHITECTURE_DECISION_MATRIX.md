# Architecture Decision Matrix

Capability scores from source inspection (2026-08-30). Scale: **none / thin / solid / mature**.

This is a design input, not a feature shopping list.

| Capability | OpenBB | Qlib | VN.Py | Hummingbot | StockSharp | OpenAlgo | QuantDinger | Lumibot | TradingAgents |
|---|---|---|---|---|---|---|---|---|---|
| Data ingest / normalize | mature | solid | solid | solid | mature | solid | solid | solid | thin |
| Point-in-time / leakage control | thin | solid | thin | none | thin | none | thin | thin | thin |
| Feature / factor engine | none | mature | solid (alpha) | none | thin | none | thin | thin | none |
| ML workflow | none | mature | solid | none | thin | none | thin | none | none |
| Backtest (costs, fills) | none | solid | solid | solid | mature | thin (analyzer) | solid | solid | thin |
| Portfolio construction | none | solid | thin | thin | solid | thin | thin | thin | thin |
| Risk firewall | none | thin | thin | solid (executors) | solid | thin | solid | thin | thin (LLM) |
| Execution / OMS | none | thin | mature | mature | mature | solid | solid | solid | none |
| Broker abstraction | n/a | none | mature (gateway) | mature | mature | mature (IN) | solid | solid | none |
| Event engine | none | thin | mature | mature | mature | thin | solid | thin | graph |
| AI agents | MCP surface | none | none | Condor (external) | none | MCP | product AI | optional | mature |
| Experiment tracking | none | mature | thin | none | thin | none | solid | thin | decision log |
| Observability / audit | thin | thin | thin | solid | solid | solid | mature | thin | thin |
| Local-first | solid | solid | solid | solid | solid | solid | mature | solid | solid |
| Indian brokers | none | none | none | none | none | mature | unknown | none | none |

## What QUANT LAB takes

| From | Principle |
|---|---|
| Qlib | Dataset + feature + model + experiment recorder; PIT timestamps |
| OpenBB | Provider protocol; no vendor types in domain |
| VN.Py | Event bus; gateway ABC; order/position objects |
| Hummingbot | Executor ≠ strategy; paper connector; order states |
| StockSharp | Rich instrument model |
| OpenAlgo | Indian broker adapter *behind* our gateway |
| QuantDinger | Postgres canonical; workers; fail-closed live; audit |
| Lumibot | One strategy interface across backtest/paper/live |
| TradingAgents | Research roles + decision logs; never live authority |
| Jansen / financial ML | Walk-forward, leakage tests, cost-aware validation |

## What QUANT LAB refuses

- Copying Qlib/OpenBB/VN.Py modules
- AGPL OpenBB source inside this tree
- Autonomous LLM order placement
- Live trading as a default
