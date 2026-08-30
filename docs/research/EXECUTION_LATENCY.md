# Execution latency

Decision at session T; eligible fill at T+Δt sessions. No fill before market arrival.

Latency itself must not be chosen from future prices. `future_latency` FAILs. `pre_arrival_fill` FAILs.

Zero latency is a configured assumption, not evidence of instantaneous NSE matching.

CLI: `quantlab execution latency`.
