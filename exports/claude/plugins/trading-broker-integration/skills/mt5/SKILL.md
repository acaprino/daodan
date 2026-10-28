---
name: mt5
description: >
  Knowledge base for the official API, its polling model, and Windows-side production concerns.
  TRIGGER WHEN: building, implementing, writing, coding, creating, optimizing, or debugging MT5 or MetaTrader 5 trading systems with Python, including the aiomql and ZeroMQ bridge alternatives.
  DO NOT TRIGGER WHEN: the broker is Interactive Brokers (use ibkr), or the question is about
  strategy design rather than the terminal and its API.
---

<daodan_host_binding host="claude">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Bodies name operations, never tools: repository read, file discovery, content
search, repository write, repository edit, shell execution, network fetch, network
search, user question and worker dispatch. The host binding below maps each one to
a registered tool. An operation it leaves unbound, or whose tool is absent from
this session, is unavailable: report it as missing, never search for a tool named
after the operation.

Claude binding: repository read, file discovery and content search use Read, Glob
and Grep; repository write and repository edit use Write and Edit; shell execution
uses Bash; network fetch uses WebFetch and network search uses WebSearch; a user
question uses AskUserQuestion. Pass the executable string in Bash's
command field, and use its registered timeout/background schema. Worker dispatch
uses the available native Agent mechanism and its registered agent-selection and
prompt fields. Do not turn a prose role label into an invented role argument.
Inherit the session model unless the declared workflow and active schema permit an
override. Load installed skills by qualified ID; named roles use their owning
plugin's agent identity, while workflow entries use /<plugin>:<workflow>.
Required foreign providers use Claude's marketplace/install commands:
claude plugin marketplace add <source>, then claude plugin install <provider>@<marketplace>.
A provider that is installed but disabled is enabled with
claude plugin enable <provider>@<marketplace>; check `claude plugin list --json`
before the first phase, and stop with that command when any plugin of this
package's dependency closure, direct or transitive, is off.
A declared package MCP server is configured through the generated MCP manifest;
still check its tools are actually available in the active session.

The executing agent and its coordinator own continuation, recovery, verification
and delivery. Skills supply knowledge and method instructions; they are not
executors or a runtime persistence mechanism.

Resolve each component by kind and exact installed identity. A role is dispatched
as a worker, a skill loads instructions, and a workflow starts its declared method.
Kernel owner-qualified skill references are logical provider identities: resolve
them to the actual host registry name and verified installed provider path. Do not
invent a registry string by adding an owner's prefix when the host does not use it.
Do not load an agent identity as a skill or execute a workflow name as a shell
command. Declared required foreign providers remain mandatory. If a required
provider or capability (including required MCP access or isolation) is unavailable,
stop its dependent phase and report the missing capability. Optional external
providers follow the method's declared selection and absence behavior; their
absence alone does not block the base workflow. Report any explicitly requested
but unavailable provider contribution as unfulfilled and continue independent
work. Do not install a different host's plugin or
substitute unrelated skills to claim coverage.

Shell execution alone does not establish interactive stdin. Before a capture or
checkpoint, use an available session-control mechanism. When stdin is unavailable,
keep user-driven capture in a supported background process with bounded output and
an explicit stop signal controlled by the coordinator after the user's completion
message. Close owned browser/process resources on completion or cancellation.

Continue working within the current authorization while the requested result is
achievable. After a tool error, inspect its cause, correct the relevant input or
implementation, retry when justified and verify the outcome; never repeat a
failing action blindly. Do not close the turn with a promise or a partial result
when an authorized next step can still produce or verify the requested result.
Stop only for a documented real impediment, a missing required capability, an
unresolved human decision or the caller's stop request. At that boundary, report
completed results, remaining work and the concrete prerequisite for continuation;
continue any independent work that the blocker does not prevent.

A tool's successful exit, a worker stop or an idle session is not the deliverable.
Return final text naming observed findings, artifact paths, executed checks and
blockers. An empty worker result is missing delivery: inspect or resume that worker
when permitted, or record failure. Verify required artifacts and candidate gates
before marking the requested outcome complete.

This is an execution binding, not a rewrite of source examples. Preserve programming
language fences, domain code and host APIs that are the subject of marketplace-ops
or agent-sdk-builder. A host-as-subject API is not a tool provided to this session.
Compiled binding and static checks do not prove an installed host executed a run.
</daodan_host_binding>

# MetaTrader 5 Python Algotrading

Knowledge base for building production-grade algorithmic trading systems with MetaTrader 5 Python API.

## What varies per broker

MetaTrader 5 is one piece of software; the broker behind a given login decides most of what an
integration actually has to handle. Nothing below is restated in full here, each item is
detailed in the file already named for it, because a reader chasing the symptom will already be
looking there:

- **Order execution parameters.** Fill mode, stops level, freeze level, execution mode and
  volume limits are broker- and symbol-specific and must be queried at runtime rather than
  assumed. See `order-execution.md`, and the Fill mode and Account mode rows of Key Decision
  Points below.
- **Data quality and coverage.** Tick volume, tick history depth and tick fidelity differ
  between ECN brokers and market makers for the same instrument, which makes cross-broker
  comparison invalid. See `data-feed-historical.md`.
- **Account and margin mode.** Netting, hedging and exchange margin modes are a broker setting,
  not a code choice, read at startup from `account_info().margin_mode`. See the Account mode
  row of Key Decision Points below.

None of this is optional hardening. A value correct for one broker is routinely wrong for the
next, which is the reason this plugin's scope is `multi-broker-platform` rather than
`single-broker`: nothing in this skill is measured against one broker's behaviour and then
offered as true of MetaTrader 5 in general.

## When to Use

- Connecting to MT5 terminal via the official Python API
- Building polling-based event systems (on_tick, on_new_candle, on_position)
- Executing orders with correct fill modes (FOK, IOC, Return)
- Downloading historical data (copy_rates, copy_ticks)
- Handling MT5 disconnections and terminal restarts
- Deploying MT5 bots on Windows with process monitoring
- Choosing between official API, aiomql, and ZeroMQ bridge

## Quick Start

For 80% of use cases, start with:
1. **Library**: `pip install MetaTrader5` (official) or `pip install aiomql` (async wrapper)
2. **Connection**: `mt5.initialize(path=..., login=..., server=..., password=...)`
3. **Event system**: polling loop with candle/tick/position change detection
4. **Orders**: `order_check()` before `order_send()`, always detect fill mode dynamically
5. **Risk**: server-side SL/TP on every position (non-negotiable)
6. **Resilience**: health check every 30-60s, psutil process monitoring, exponential backoff

Then harden incrementally:
- Silent errors - wrap every API call with None check + last_error()
- Fill mode rejections (10030) - dynamic filling_mode detection per symbol
- Terminal crashes - psutil watchdog + subprocess restart
- Weekend handling - datetime.weekday() sleep mode

## Reference Materials

- `api-architecture.md` - MT5 Python API architecture, 32 functions, named pipes IPC, MQL5 EA vs Python, library comparison
- `event-system-polling.md` - polling patterns, new candle detection, tick monitoring, position tracking, concurrency rules
- `order-execution.md` - order_send, fill modes (FOK/IOC/Return), hedging vs netting, retcodes, risk checks, magic numbers
- `data-feed-historical.md` - copy_rates, copy_ticks, depth, timezone caveats, caching, data quality, broker differences
- `production-resilience.md` - disconnection handling, reconnection, weekend management, Windows deployment, community resources

## Symptoms to entry points

| Symptom | Read |
|---|---|
| An API call returned `None` and nothing was logged | `api-architecture.md` |
| Order rejected with retcode 10030 | `order-execution.md` |
| Positions netted when hedging was expected | `order-execution.md` |
| A tick or candle handler never fires | `event-system-polling.md` |
| Bars disagree with the chart, or timestamps look shifted | `data-feed-historical.md` |
| The terminal is running but the API answers nothing | `production-resilience.md` |
| Everything stops on Saturday and resumes wrong on Monday | `production-resilience.md` |

## Key Decision Points

| Decision | Default | Upgrade When |
|----------|---------|-------------|
| Library | Official MetaTrader5 | Need async: aiomql. Need true streaming: ZeroMQ bridge |
| Event model | Polling (1-5s interval) | Tick-sensitive: poll 100-250ms. True events: ZeroMQ EA bridge |
| Fill mode | Detect dynamically per symbol | Never hardcode - changes between brokers/symbols |
| Account mode | Hedging (most forex brokers) | Check account_info().margin_mode at startup |
| Data caching | Parquet + Zstandard | Tick data - partition by day/month |
| Concurrency | asyncio (single thread) | Multi-account - separate processes per terminal |
| Backtesting | Python framework (Backtrader, Backtesting.py) | Need MT5 tester - MQL5 EA wrapper |
| SL/TP | Server-side always | Python trailing only as supplement, never as sole protection |
