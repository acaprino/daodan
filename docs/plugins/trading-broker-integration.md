# Trading Broker Integration Plugin

> Broker integration for algorithmic trading in Python: Interactive Brokers via the TWS API and ib_async across equities, options, futures, FX, CFDs and crypto (contracts and market rules, order types and TIF/fill-mode capability resolution, brackets, a classified catalog of all 458 published TWS message codes, venue-behaviour verification tooling, reconnection resilience, deployment on Windows, Linux, macOS and Docker), MetaTrader 5 via the official synchronous API (polling-based event systems, order execution with fill modes, historical data, the aiomql async framework, a ZeroMQ bridge, Windows production deployment), and the vendor-neutral vocabulary shared between them: five access archetypes, the single-broker/multi-broker-platform axis, a reference order-lifecycle state machine, session and recovery patterns, and a six-rank evidence ladder with provenance tags.

Command examples and named tools in this guide use Claude notation. For other
hosts, use the entry points and bindings in the source-derived reference below
and [host setup](../hosts.md).

## Agents

### `ibkr-architect`

Expert in Interactive Brokers algotrading system design, implementation, and debugging.

| | |
|---|---|
| **Model** | `inherit` |
| **Tools** | `Read, Write, Edit, Bash, Glob, Grep, WebFetch, WebSearch` |
| **Use for** | Building IB trading bots, connecting to TWS/IB Gateway, implementing market data subscriptions, designing order execution logic, handling IB reconnection, diagnosing silent order/close failures (wrong-side closes, preset cancellations, swallowed rejections), deploying IB trading systems on Windows |

**Invocation:**
```
Use the ibkr-architect agent to [design/implement/debug] [trading component]
```

---

### `mt5-architect`

Expert in MetaTrader 5 Python algotrading system design, implementation, and debugging.

| | |
|---|---|
| **Model** | `inherit` |
| **Tools** | `Read, Write, Edit, Bash, Glob, Grep, WebFetch, WebSearch` |
| **Use for** | Building MT5 trading bots, connecting to MT5 terminal via Python, implementing polling event loops, executing orders with correct fill modes, handling MT5 disconnections, deploying MT5 bots on Windows |

**Invocation:**
```
Use the mt5-architect agent to [design/implement/debug] [trading component]
```

---

## Skills

### `broker-vocabulary`

The vocabulary that is the same for every broker: what kind of access path a system has, how to model an order's life without borrowing one vendor's words for it, and what a claim about a venue is actually worth.

| | |
|---|---|
| **Trigger** | Comparing brokers or integration paths, starting an integration against a broker with no dedicated skill in this plugin, or naming what kind of access path a system uses |

**Reference documents:** access-archetypes, order-lifecycle-reference-model, session-and-recovery, evidence-and-probes.

---

### `ibkr`

Authoritative reference for Interactive Brokers integration in Python, across every asset class, with tooling to verify venue behaviour against a paper Gateway instead of guessing.

| | |
|---|---|
| **Trigger** | Building, auditing or debugging anything that talks to TWS or IB Gateway via the TWS API and ib_async: contracts, market data, orders, brackets, error codes, reconnection, deployment, or a question about how IBKR actually behaves |

**Reference documents:** tws-api-architecture, contracts-and-instruments, event-driven-data, order-execution, order-types-and-attributes, bracket-orders, order-lifecycle-contracts, error-codes-and-verdicts, account-state-and-pnl, venue-boundary-failure-modes, venue-questions-and-probes, reconnection-resilience, gateway-automation, gateway-verification.

---

### `mt5`

Knowledge base for the official MetaTrader 5 API, its polling model, and Windows-side production concerns.

| | |
|---|---|
| **Trigger** | Building, implementing, optimizing, or debugging MT5 trading systems with Python, including the aiomql and ZeroMQ bridge alternatives |

**Reference documents:** api-architecture, event-system-polling, order-execution, data-feed-historical, production-resilience.

---

## Commands

### `/trading-broker-integration:ibkr-audit`

Audit an existing Interactive Brokers trading system for reliability, error handling, and production readiness. Scopes the asset classes and account entity first, which decides the checks that apply, then covers connection, market data, orders, close path and netting, account state, positions and PnL, capability assumptions and their provenance, terminal preset config, error handling, event listeners, venue boundary, reconnection, historical data integrity, and production hardening.

```
/trading-broker-integration:ibkr-audit [path-or-description]
```

---

### `/trading-broker-integration:ibkr-verify`

Answer a question about IBKR behaviour with evidence instead of a guess: whether IBKR supports something, why an order was refused, what a code means, or a claim about venue behaviour verified against a real gateway. Walks a fixed evidence ladder (rung 0: is it a message code, looked up in the shipped code table; rung 1: capability list; rung 2: documentation; rung 3: probe against a paper Gateway; rung 4: report as unresolved) and reports which rung produced the answer.

```
/trading-broker-integration:ibkr-verify [question, code, or contract]
```

---

### `/trading-broker-integration:mt5-audit`

Audit an existing MetaTrader 5 trading system for reliability, error handling, and production readiness. Covers connection setup, event/polling loop structure, order execution, data fetching, error handling, reconnection, logging, thread safety, and production hardening.

```
/trading-broker-integration:mt5-audit [path-or-description]
```

---

**Related:** [python-development](python-development.md) (Python best practices for trading code)

<!-- daodan:reference:start -->
## Source-derived reference

Generated by `python scripts/sync_plugin_docs.py`. Edit the kernel and regenerate
this block; keep explanations above it. `--check` detects stale references.

**Version:** `2.1.3`. **Source:** [plugin.toml](<../../plugins/trading-broker-integration/plugin.toml>).

### Required dependencies

Every listed plugin dependency is mandatory. Transitive requirements remain
mandatory when using this plugin alone. The local closure includes this plugin.

| Requirement | Plugins |
|---|---|
| Direct local | None |
| Direct external | None |
| Local closure (1) | [trading-broker-integration](<trading-broker-integration.md>) |
| External closure (0) | None |

External bundles are separate upstream installations, not copied local skills.
See [host setup](<../hosts.md>) for selection and availability requirements.

**Required capabilities:** `repository.read`, `shell.execute`, `repository.write`, `network.fetch`, `contexts.isolate`, `roles.dispatch`.
**Optional capabilities:** `execution.parallel`.
Optional capabilities are host mechanisms, not optional local plugin dependencies.

### Registered components

Names below are kernel IDs. Host entry points and paths follow the adapter
mapping in [the host reference](<../hosts.md>).
The source links carry the complete instructions and accepted arguments.

| Kind | ID | Purpose and trigger | Source |
|---|---|---|---|
| Skill | `trading-broker-integration:broker-vocabulary` | Vendor-neutral vocabulary for programmatic broker integration: the five access archetypes, the second axis separating a single broker from a multi-broker platform, the reference order state machine, session and recovery, and the evidence ladder that decides what a claim about a venue is worth. TRIGGER WHEN: comparing brokers or integration paths, starting an integration against a broker with no dedicated skill, or naming what kind of access path a system uses. DO NOT TRIGGER WHEN: the question is about one specific broker that has its own skill (use the ibkr or mt5 skill), or about strategy, backtesting, or portfolio construction. | [broker-vocabulary](<../../plugins/trading-broker-integration/skills/broker-vocabulary/SKILL.md>) |
| Skill | `trading-broker-integration:ibkr` | Authoritative reference for Interactive Brokers integration in Python, across every asset class, with tooling to verify venue behaviour against a paper Gateway instead of guessing. TRIGGER WHEN: building, auditing or debugging anything that talks to TWS or IB Gateway via the TWS API and ib_async: contracts, market data, orders, brackets, error codes, reconnection, deployment, or a question about how IBKR actually behaves. DO NOT TRIGGER WHEN: MetaTrader 5 (use mt5), or the IBKR Web API with no TWS connection. | [ibkr](<../../plugins/trading-broker-integration/skills/ibkr/SKILL.md>) |
| Skill | `trading-broker-integration:mt5` | Knowledge base for the official API, its polling model, and Windows-side production concerns. TRIGGER WHEN: building, implementing, writing, coding, creating, optimizing, or debugging MT5 or MetaTrader 5 trading systems with Python, including the aiomql and ZeroMQ bridge alternatives. DO NOT TRIGGER WHEN: the broker is Interactive Brokers (use ibkr), or the question is about strategy design rather than the terminal and its API. | [mt5](<../../plugins/trading-broker-integration/skills/mt5/SKILL.md>) |
| Role | `trading-broker-integration:ibkr-architect` | Authority on Interactive Brokers integration: contracts, orders, brackets, data, error verdicts, resilience and deployment, across equities, options, futures, FX, CFDs and crypto. TRIGGER WHEN: building or debugging anything on the TWS API with ib_async, or answering a question about how IBKR behaves. DO NOT TRIGGER WHEN: auditing an existing system end to end (use /trading-broker-integration:ibkr-audit), MetaTrader 5 (use mt5), or broker-agnostic strategy logic. | [ibkr-architect](<../../plugins/trading-broker-integration/roles/ibkr-architect.md>) |
| Role | `trading-broker-integration:mt5-architect` | Architect, harden, and troubleshoot automated retail-broker systems. TRIGGER WHEN: building, implementing, writing, coding, or creating MT5 trading bots, connecting to MT5 terminal via Python, implementing polling event loops, executing orders with correct fill modes, handling MT5 disconnections, deploying MT5 bots on Windows, working with MetaTrader5/aiomql/MQL5-JSON-API/ZeroMQ bridge code, or comparing MT5 vs IBKR approaches. | [mt5-architect](<../../plugins/trading-broker-integration/roles/mt5-architect.md>) |
| Workflow | `trading-broker-integration:ibkr-audit` | Report reliability and production-readiness defects, plus the venue assumptions nobody checked. TRIGGER WHEN: the user asks to review, audit, or validate an IB or TWS trading system: contracts, orders, brackets, pacing, error handling, reconnection, deployment. DO NOT TRIGGER WHEN: building from scratch (use ibkr-architect), answering a single behaviour question (use /trading-broker-integration:ibkr-verify), or MetaTrader 5 (use /trading-broker-integration:mt5-audit). | [ibkr-audit](<../../plugins/trading-broker-integration/workflows/ibkr-audit.md>) |
| Workflow | `trading-broker-integration:ibkr-verify` | Answer a question about IBKR behaviour with evidence instead of a guess. TRIGGER WHEN: the user asks whether IBKR supports something, why an order was refused, what a code means, or wants a claim about venue behaviour verified against a real gateway. DO NOT TRIGGER WHEN: auditing a whole codebase (use /trading-broker-integration:ibkr-audit), or designing a system from scratch (use the ibkr-architect agent). | [ibkr-verify](<../../plugins/trading-broker-integration/workflows/ibkr-verify.md>) |
| Workflow | `trading-broker-integration:mt5-audit` | Report on the reliability, error handling, and production readiness of an existing system. TRIGGER WHEN: the user asks to review, audit, or validate an MT5 Python trading bot (polling loops, fill modes, reconnection, order retcodes, Windows deployment). DO NOT TRIGGER WHEN: building from scratch (use the mt5-architect agent), or auditing an IB system (use /trading-broker-integration:ibkr-audit). | [mt5-audit](<../../plugins/trading-broker-integration/workflows/mt5-audit.md>) |

### Workflow contracts

Contracts describe observable outputs; Markdown bodies define decisions,
flags, safety gates and execution. Declared `invoke` execution is unsupported.

#### `trading-broker-integration:ibkr-audit`

**Arguments:** `[path-or-description]`

| Contract | Value |
|---|---|
| Inputs | `repository` |
| Outcomes | `ibkr-audit-completed` |
| Artifacts | `ibkr-audit-report` |
| Schemas | None declared |
| Declared workers | None |
| Composed worker isolation | See phase isolation below |
| Task-specific isolated workers | Not declared |
| Sidecar | [ibkr-audit.toml](<../../plugins/trading-broker-integration/workflows/ibkr-audit.toml>) |

| Phase | Needs | Dispatch | Isolation | Join | Concurrency |
|---|---|---|---|---|---|
| `run` | None | None | `shared` | None declared | `preferred` |

#### `trading-broker-integration:ibkr-verify`

**Arguments:** `[question, code, or contract]`

| Contract | Value |
|---|---|
| Inputs | `repository` |
| Outcomes | `ibkr-verify-completed` |
| Artifacts | `ibkr-verify-report` |
| Schemas | None declared |
| Declared workers | None |
| Composed worker isolation | See phase isolation below |
| Task-specific isolated workers | Not declared |
| Sidecar | [ibkr-verify.toml](<../../plugins/trading-broker-integration/workflows/ibkr-verify.toml>) |

| Phase | Needs | Dispatch | Isolation | Join | Concurrency |
|---|---|---|---|---|---|
| `run` | None | None | `shared` | None declared | `preferred` |

#### `trading-broker-integration:mt5-audit`

**Arguments:** `[path-or-description]`

| Contract | Value |
|---|---|
| Inputs | `repository` |
| Outcomes | `mt5-audit-completed` |
| Artifacts | `mt5-audit-report` |
| Schemas | None declared |
| Declared workers | None |
| Composed worker isolation | See phase isolation below |
| Task-specific isolated workers | Not declared |
| Sidecar | [mt5-audit.toml](<../../plugins/trading-broker-integration/workflows/mt5-audit.toml>) |

| Phase | Needs | Dispatch | Isolation | Join | Concurrency |
|---|---|---|---|---|---|
| `run` | None | None | `shared` | None declared | `preferred` |

### Host exports

Package paths and coordination are derived from the host adapters. `native`
and `adapted` describe bindings, not successful installed-host execution.

The selected strategy is an adapter binding even for a flat workflow body.
A dispatch harness is rendered only for declared method workers, task-specific
workers or phase fan-out; the host reference explains the entry artifacts.

| Host | Package | Binding | Selected workflow strategy |
|---|---|---|---|
| claude | [exports/claude/plugins/trading-broker-integration](<../../exports/claude/plugins/trading-broker-integration>) | `native` | `ibkr-audit: native-team`, `ibkr-verify: native-team`, `mt5-audit: native-team` |
| copilot | [exports/copilot/plugins/trading-broker-integration](<../../exports/copilot/plugins/trading-broker-integration>) | `native` | `ibkr-audit: parallel-subagents`, `ibkr-verify: parallel-subagents`, `mt5-audit: parallel-subagents` |
| codex | [exports/codex/plugins/trading-broker-integration](<../../exports/codex/plugins/trading-broker-integration>) | `adapted` | `ibkr-audit: parallel-subagents`, `ibkr-verify: parallel-subagents`, `mt5-audit: parallel-subagents` |
| pi | [exports/pi/plugins/trading-broker-integration](<../../exports/pi/plugins/trading-broker-integration>) | `adapted` | `ibkr-audit: parallel-subagents`, `ibkr-verify: parallel-subagents`, `mt5-audit: parallel-subagents` |
| opencode | [exports/opencode/plugins/trading-broker-integration](<../../exports/opencode/plugins/trading-broker-integration>) | `native` | `ibkr-audit: parallel-subagents`, `ibkr-verify: parallel-subagents`, `mt5-audit: parallel-subagents` |

<!-- daodan:reference:end -->
