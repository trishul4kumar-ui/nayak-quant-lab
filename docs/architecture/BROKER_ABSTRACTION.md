# Broker Abstraction

Broker access is protocol-based (`BrokerAdapter`). The core does not depend on a vendor SDK. `quantlab.brokers` (ADR-007) remains the original paper gateway with order methods. `quantlab.broker_gateway` is a separate read-only account boundary.

Adapters expose: connect, disconnect, health, account, positions, holdings, margins, orders, fills, trades, instrument metadata, session status. There is no `place_order` on the protocol.
