<daodan_host_binding host="codex">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Codex binding: the adapter binds repository read to read_file, writes to
apply_patch and shell execution to shell; use the equivalent registered tools of
the active Codex runtime and their actual fields. In particular, a shell example's
command, timeout and background fields are not automatically another runtime's
cmd, yield_time_ms or session controls.
Start the runtime's available isolated subagent mechanism with the complete
rendered role body in its task prompt. Role Markdown and generated dispatch bodies
are resources, not registered skills or a native role/subagent_type parameter.
Use only declared role bindings and report an unavailable isolation mechanism.
Load installed skills by their advertised exact IDs; workflow skills carry the
<workflow>-workflow suffix. Named-agent examples do not override inline delivery.
Required foreign providers use Codex's marketplace/install commands:
codex plugin marketplace add <source>, then codex plugin add <provider>@<marketplace>.
Register plugin-declared MCP servers through the active host's MCP configuration
using the generated server command. Do not assume registration makes every tool
available to a restricted worker.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.

The executing agent and its coordinator own continuation, recovery, verification
and delivery. Skills supply knowledge and method instructions; they are not
executors or a runtime persistence mechanism.

Resolve each component by kind and exact installed identity. A role is dispatched
as a worker, a skill loads instructions, and a workflow starts its declared method.
Kernel owner-qualified skill references are logical provider identities: resolve
them to the actual host registry name and verified installed provider path. Do not
invent a registry string by adding an owner's prefix when the host does not use it.
Do not load an agent identity as a skill or execute a workflow name as a shell
command. Named foreign providers remain mandatory. If an installed provider, MCP
server or required isolation mechanism is unavailable, stop its dependent phase
and report the missing capability. Do not install a different host's plugin or
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

# MT5 Python API Architecture

The official `MetaTrader5` PyPI package (by MetaQuotes) talks to the MT5 terminal via **Windows named pipes** (local IPC). Synchronous request-response only, no callbacks, no streaming. Polling is the only pattern. Current version mirrors the platform build (e.g. 5.0.5735), Python 3.6-3.14.

## When to use

Building any Python algotrading system on MT5. For true event-driven (push) behavior you need an MQL5 EA that bridges to Python via ZeroMQ - see "Alternative libraries" below.

## Hard constraints (memorize before designing)

- **Windows-only.** Named pipes IPC has no native cross-platform path. Linux options below are workarounds.
- **No exceptions, no docstrings, no logging, no context manager.** Every call returns `None` on failure - check return value AND `mt5.last_error()` after every call.
- **One Python process = one MT5 terminal connection.** No multi-tenant model.
- **Not thread-safe.** The pipe is single - concurrent access from threads = race conditions, crashes, or corrupted data. Serialize calls or use a single dedicated worker thread.
- **No callbacks / push events.** Pure request-response; you build your own event loop on top of polling.
- **No Strategy Tester access.** Backtesting is MQL5-only; from Python use Backtrader / Backtesting.py with historical data downloaded via the API.

## Gotchas

- **Errors are silent.** `order_send()` returning `None` is a hard failure - but the API doesn't raise. `mt5.last_error()` returns `(code, description)`. Wrap every call in a check.
- **MQL5 EAs and Python coexist** on the same terminal. EAs run on charts; Python operates externally. The terminal option **"Disable automatic trading via external Python API"** blocks Python trading (retcode 10027) while leaving EAs active - a common cause of "my bot stopped working" after broker config changes.
- **Strategy Tester blocks all socket functions.** Inside the tester, MQL5 EAs cannot communicate with Python via sockets. There is no way to backtest a Python strategy through the MT5 tester.
- **`pip install MetaTrader5` ships a compiled C library** - the install is fast but it must match the platform's Python ABI. Mismatch = silent import success but `initialize()` returns False with no useful error.
- **The API exposes only 32 functions** - if you can't see it in the docs index, it's not there. There is no `OnTick()`, no event subscription, no async variant.

## Library choice

| Library | Streaming | Async | Cross-platform | Status | Best for |
|---------|-----------|-------|----------------|--------|----------|
| **MetaTrader5** (official) | Polling | Sync | Windows | Active | Direct access, low overhead |
| **aiomql** | Async polling | asyncio | Windows | Active | Best Python-pure async framework |
| **MQL5-JSON-API** (ZMQ) | **True streaming** | Yes | Any | Moderate | True event-driven via MQL5 EA bridge |
| **metaapi-cloud-sdk** | WebSocket | Yes | Any | Active (paid) | Cross-platform, paid cloud |
| **mt5linux** / **pymt5linux** | Polling | Sync | Linux (Wine + RPyC) | Inactive / fork | Linux dev, not production |

Avoid: `pymt5adapter` (deprecated), `pymt5` (gateway-only).

## Comparison with IBKR TWS API (mental model)

| Aspect | MT5 Python | IBKR TWS API |
|--------|-----------|--------------|
| Architecture | Sync polling | Event-driven callbacks |
| Rate limits | None documented (local IPC, ~63us per call) | 50 msg/sec, pacing rules |
| Data cost | Included with account | Paid exchange subscriptions |
| Data source | Broker-dependent | Exchange-sourced |
| Cross-platform | Windows only | Windows / Linux / macOS |
| Streaming | Polling (or ZMQ bridge) | Native callbacks |

If you're coming from IBKR expecting `EWrapper` callbacks, **you build the entire event system from scratch on MT5** (see `event-system-polling.md`).

## Official docs

- Python API home: https://www.mql5.com/en/docs/python_metatrader5
- Per-function reference: `https://www.mql5.com/en/docs/python_metatrader5/mt5{functionname}_py`
- MetaEditor + Python integration: https://www.metatrader5.com/en/metaeditor/help/development/python
- Release notes: https://www.metatrader5.com/en/releasenotes
- aiomql: https://github.com/Ichinga-Samuel/aiomql
- MQL5-JSON-API (ZMQ bridge): https://github.com/khramkov/MQL5-JSON-API

## Related

- `event-system-polling.md` - how to build an event loop on top of polling
- `data-feed-historical.md` - the `copy_rates_*` and `copy_ticks_*` family
- `order-execution.md` - `order_send()`, fill modes, retcode handling
- `production-resilience.md` - Windows deployment, watchdog, weekend gate
