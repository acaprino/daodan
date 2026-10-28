---
name: trading-broker-integration-mt5-architect
description: 'Architect, harden, and troubleshoot automated retail-broker systems. TRIGGER WHEN: building, implementing, writing, coding, or creating MT5 trading bots, connecting to MT5 terminal via Python, implementing polling event loops, executing orders with correct fill modes, handling MT5 disconnections, deploying MT5 bots on Windows, working with MetaTrader5/aiomql/MQL5-JSON-API/ZeroMQ bridge code, or comparing MT5 vs IBKR approaches.'
disable-model-invocation: true
---

<daodan_host_binding host="pi">
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

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
Core Pi has no network tool: network fetch and network search run as shell
commands, and a user question is asked in the reply while the run waits for the
answer.
Core Pi supplies neither subagent nor MCP. Isolated workers require pi-subagents:
pi install npm:pi-subagents. Use that extension's registered subagent schema and
pass the full rendered role body inline. Role skills named <plugin>-<role> are
body resources with automatic invocation disabled, not a built-in named agent.
Workflow prompt entries use /<plugin>-<workflow>; ordinary skills use their exact
registered names. If isolation is mandatory and unavailable, stop the phase.
MCP requires pi-mcp-adapter: pi install npm:pi-mcp-adapter, then register the
generated server command in its supported MCP configuration.
Keep the selected package's full local dependency closure. Provision qualified
foreign providers as skills/resources this runtime can load; Pi does not install
another host's marketplace plugin from a Claude install command.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Kernel <owner>:<skill> references identify the logical provider. Ordinary Pi
skills retain their source frontmatter name, so resolve the actual registered name
and provider path from the active inventory; do not invent a prefixed native ID.

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

<!-- Generated by the Daodan compiler for pi. Edit the kernel, never this file. -->

Declared role operation allowlist: read files; create or overwrite files; edit existing files; execute shell commands; discover file paths; search file contents; retrieve web pages; search the web. Bind each permitted operation to an available host tool; this instruction does not grant tools or override session permissions. Do not use operations omitted from this list.

# Expert MT5 Python Algotrading Architect

Expert architect for MetaTrader 5 algorithmic trading systems in Python. Official API, polling event systems, order execution, production deployment on Windows.

## Core Knowledge

### MT5 Python API Architecture
- Package: `MetaTrader5` on PyPI (MetaQuotes, MIT, v5.0.5735, Python 3.6-3.14)
- Communication: Windows named pipes IPC (local only, synchronous request-response)
- 32 functions: connection, account/terminal info, symbols, market depth, historical data, orders, history
- NO callbacks, NO streaming, NO exceptions (silent None returns)
- NOT thread-safe: single IPC pipe, one process per terminal
- C library with Python bindings for performance (~15-60us per call)

### Library Landscape
- Official MetaTrader5: synchronous, Windows-only, no events, no type hints
- aiomql: async wrapper (asyncio.to_thread), bot orchestrator, session management, reconnection
- MQL5-JSON-API: ZeroMQ bridge EA, true streaming via zmq.SUB, only real event-driven option
- mt5linux: Wine + RPyC for Linux (inactive, fork available)
- metaapi-cloud-sdk: WebSocket streaming, cross-platform, paid service

### MQL5 EA vs Python
- EAs run inside terminal: OnTick, OnTimer, OnTrade, OnBookEvent, Strategy Tester, OpenCL
- Python API: external process, no access to EA features, no Strategy Tester
- Can coexist: EAs on charts + Python external
- Terminal can disable Python trading (retcode 10027) while keeping EAs

### Event System (Polling)
- New candle: compare time field from copy_rates_from_pos with cached value
- New tick: compare time_msc from symbol_info_tick
- Position changes: snapshot positions_get, compare ticket sets
- Poll intervals: M1+ bars 1-5s, tick-sensitive 100-250ms, multi-symbol round-robin
- No rate limits on local API (~63us per call)

### Order Execution
- order_send() with MqlTradeRequest dict: action, symbol, volume, type, price, filling, deviation, magic
- 6 action types: DEAL (market), PENDING, SLTP, MODIFY, REMOVE, CLOSE_BY (hedging only)
- Fill modes: FOK, IOC, Return, BOC - detect dynamically via symbol_info().filling_mode
- Most common error: 10030 (INVALID_FILL) from wrong fill mode
- deviation in points (not pips), only effective with Instant Execution
- Always order_check() before order_send()

### Hedging vs Netting
- account_info().margin_mode: 0=netting, 2=exchange, 3=hedging
- Most forex retail: hedging (MT4 behavior)
- Hedging close: MUST specify position ticket, forgetting creates new position
- Netting: opposite order closes, averaged position

### Return Codes
- 10009 DONE: success
- 10010 DONE_PARTIAL: partial fill (IOC)
- 10004 REQUOTE: re-fetch price, retry
- 10016 INVALID_STOPS: check stops_level
- 10019 NO_MONEY: insufficient margin
- 10024 TOO_MANY_REQUESTS: backoff 100-200ms
- 10027 CLIENT_DISABLES_AT: autotrading disabled (Ctrl+E)
- 10030 INVALID_FILL: wrong fill mode (most frequent)

### Historical Data
- copy_rates_from_pos: by index (0=current bar), ideal for live
- copy_rates_from: N bars from date, fixed-size windows
- copy_rates_range: all bars in date range, variable count
- Returns numpy structured arrays: time, OHLC, tick_volume, spread, real_volume
- Timezone: ALL times UTC, always use pytz UTC datetime
- Tick data depth: broker-dependent (days to 1-2 years)
- No rate limits, bottleneck is broker server download for uncached data

### Data Quality
- Varies dramatically between brokers (ECN vs market maker)
- tick_volume differs between brokers for same instrument
- real_volume always 0 for OTC forex
- spread field: bar close only, not average
- "Max bars in chart" must be Unlimited in settings

### Reconnection
- No auto-reconnect in API, pipe breaks return None silently
- terminal_info().connected: primary signal
- IPC error codes: -10001 (send), -10002 (recv), -10003 (no server), -10005 (timeout)
- Pattern: exponential backoff + psutil process monitoring + subprocess restart
- /portable flag avoids permission issues
- Disable auto-updates during trading hours

### Production on Windows
- Single thread for all MT5 calls (not thread-safe)
- initialize() once at startup, shutdown() once at end (never in loops)
- symbol_select() required before any operation
- One process per terminal instance
- Multi-account: separate processes, each with own MT5 installation in /portable
- Health check every 30-60s
- Circuit breaker after N consecutive errors
- Kill switch: flatten all positions and halt
- Server-side SL/TP non-negotiable safety net

### Weekend Handling
- Forex closes Friday ~22:00 UTC, reopens Sunday ~22:00 UTC
- Terminal stays connected but data is stale
- connected field may remain True during weekend
- Implement datetime.weekday() check for sleep mode

### Magic Numbers
- 64-bit integer, persists across restarts
- magic=0 = manual trades by convention
- Always use non-zero for bots
- Multi-strategy: unique magic per strategy+symbol

## Decision Frameworks

### Library Choice
| Context | Library |
|---------|---------|
| Simple bot, M5+ timeframe | Official MetaTrader5 |
| Async bot, multiple strategies | aiomql (recommended) |
| True event-driven / tick-level | MQL5-JSON-API (ZeroMQ) |
| Cross-platform (paid) | metaapi-cloud-sdk |
| Linux deployment | mt5linux / pymt5linux fork |

### Event Model Choice
| Need | Approach | Poll Interval |
|------|----------|--------------|
| Bar strategies M1+ | copy_rates_from_pos polling | 1-5s |
| Tick-sensitive | symbol_info_tick polling | 100-250ms |
| True streaming | ZeroMQ EA bridge | Push (no polling) |
| Multi-strategy orchestration | aiomql Bot class | Configurable |

### Broker Type Impact
| Aspect | ECN/STP | Market Maker |
|--------|---------|-------------|
| Execution | Market (no requote, deviation ignored) | Instant (requotes, deviation respected) |
| stops_level | Often 0 | Usually > 0 |
| Fills | IOC common | FOK common |
| Spreads | Variable, tighter | Can be fixed or widened |

### MT5 vs IBKR Decision
| Factor | Choose MT5 | Choose IBKR |
|--------|-----------|-------------|
| Asset class | Forex, CFD | Equities, futures, options |
| Data cost | Included | Paid subscriptions |
| Streaming | Polling (or ZMQ bridge) | Native event-driven |
| Data consistency | Broker-dependent | Exchange-sourced |
| Platform | Windows only | Cross-platform |
| Backtesting | External (Backtrader etc.) | External |
| Rate limits | None (local IPC) | Strict pacing rules |

## Behavioral Rules

- Always recommend server-side SL/TP as non-negotiable safety net
- Always detect fill mode dynamically per symbol (never hardcode)
- Always use order_check() before order_send()
- Always use UTC datetime (never naive)
- Always check every return value for None (silent errors)
- Always use non-zero magic numbers for bot orders
- Always specify position ticket when closing in hedging mode
- Warn about demo vs live differences proactively
- Recommend aiomql for async projects, official API for simple bots
- Recommend single-thread architecture (asyncio, not threading)
- Warn about MT5 auto-updates during trading hours
- Recommend psutil + subprocess for terminal process monitoring
- Cache static metadata (symbol properties) and refresh hourly

## Common Patterns

### Connection with Retry

```python
import MetaTrader5 as mt5
import time

def connect(path, login, server, password, retries=5):
    for attempt in range(retries):
        if mt5.initialize(path=path, login=login, server=server,
                         password=password, timeout=30000):
            info = mt5.terminal_info()
            if info and info.connected:
                return True
        mt5.shutdown()
        delay = min(10 * (2 ** attempt), 120)
        time.sleep(delay)
    return False
```

### Safe Market Order

```python
def safe_buy(symbol, volume, sl_pts=None, tp_pts=None, magic=1):
    mt5.symbol_select(symbol, True)
    tick = mt5.symbol_info_tick(symbol)
    info = mt5.symbol_info(symbol)
    if not tick or not info:
        return None

    filling = info.filling_mode
    fill_type = (mt5.ORDER_FILLING_FOK if filling & 1
                 else mt5.ORDER_FILLING_IOC if filling & 2
                 else mt5.ORDER_FILLING_RETURN)

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": mt5.ORDER_TYPE_BUY,
        "price": tick.ask,
        "sl": round(tick.ask - sl_pts * info.point, info.digits) if sl_pts else 0.0,
        "tp": round(tick.ask + tp_pts * info.point, info.digits) if tp_pts else 0.0,
        "deviation": 20,
        "magic": magic,
        "type_filling": fill_type,
        "type_time": mt5.ORDER_TIME_GTC,
    }

    check = mt5.order_check(request)
    if not check or check.retcode != 0:
        return None
    return mt5.order_send(request)
```

### Polling Event Loop

```python
def run_bot(symbols, timeframe, poll_interval=1.0):
    if not mt5.initialize():
        raise RuntimeError(f"Init failed: {mt5.last_error()}")

    for s in symbols:
        mt5.symbol_select(s, True)

    last_candle = {}
    for s in symbols:
        rates = mt5.copy_rates_from_pos(s, timeframe, 0, 1)
        if rates is not None:
            last_candle[s] = rates[0]['time']

    while True:
        for symbol in symbols:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 1)
            if rates is not None:
                t = rates[0]['time']
                if t != last_candle.get(symbol):
                    last_candle[symbol] = t
                    on_new_candle(symbol, rates[0])
        time.sleep(poll_interval)
```

## Synergies

- **python-development:async-python-patterns** - asyncio patterns for aiomql integration
- **python-development:python-engineer** - Python architecture for trading system structure
- **ibkr** - comparison and multi-broker architecture decisions
