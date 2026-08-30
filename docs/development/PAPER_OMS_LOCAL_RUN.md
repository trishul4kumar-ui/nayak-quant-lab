# Paper OMS — local run

Paper OMS is local, deterministic, and paper-only.

```bash
quantlab paper create
quantlab paper plan last
quantlab paper submit last
quantlab paper fills last
quantlab paper positions PAPER-001
quantlab paper cash PAPER-001
quantlab paper reconcile last
quantlab paper tca last
quantlab paper residuals last
quantlab paper report last
```

Research aliases:

```bash
quantlab research paper-oms
quantlab research paper-execution
quantlab research order-lifecycle
quantlab research reconciliation
quantlab research paper-tca
```

`LIVE_TRADING` must remain false. `SUBMIT PAPER` on Paper OMS Lab calls `quantlab.app.paper_oms`, not a broker.

Seed names (`NSE:AAA/BBB/CCC`) and prices are architecture diagnostics, not NSE quotes.
