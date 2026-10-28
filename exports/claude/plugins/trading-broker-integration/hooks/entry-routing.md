# Entry routing: trading-broker-integration

These lines are the entry workflows and knowledge of the `trading-broker-integration` plugin. A request that matches a line runs through that entry before other work. A workflow or skill entry is invoked with the host's skill or command mechanism; an entry marked "agent to dispatch" is dispatched as an agent.

- `/trading-broker-integration:ibkr-audit`: TRIGGER WHEN: the user asks to review, audit, or validate an IB or TWS trading system: contracts, orders, brackets, pacing, error handling, reconnection, deployment.
- `/trading-broker-integration:ibkr-verify`: TRIGGER WHEN: the user asks whether IBKR supports something, why an order was refused, what a code means, or wants a claim about venue behaviour verified against a real gateway.
- `/trading-broker-integration:mt5-audit`: TRIGGER WHEN: the user asks to review, audit, or validate an MT5 Python trading bot (polling loops, fill modes, reconnection, order retcodes, Windows deployment).
- IBKR, Interactive Brokers, TWS, IB Gateway: `trading-broker-integration:ibkr`
- MT5, MetaTrader, MetaTrader 5: `trading-broker-integration:mt5`
