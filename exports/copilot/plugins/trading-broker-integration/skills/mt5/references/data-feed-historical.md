<daodan_host_binding host="copilot">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Copilot binding: repository reads use search, writes use edit, shell execution uses
runCommands and network fetch uses fetch in the adapter's tool allowlist. Custom
agent dispatch uses the agent allowlist alias; the current CLI documents a task
dispatch tool. Call the mechanism actually registered in this session, not an
allowlist alias assumed to be a callable tool.
Use each registered tool's input fields; Claude's subagent_type, role and
run_in_background fields are not a portable dispatch schema. Dispatch only the
custom agent named by the generated owner-qualified binding and agents allowlist.
An omitted tools restriction retains host defaults; an explicit list constrains
the worker and does not grant omitted shell, write or MCP tools.
Skills use their exact installed registry identity; workflows are prompt entries.
A dispatched workflow also has its generated <workflow>-coordinator custom agent.
Required foreign providers use Copilot's marketplace/install commands:
copilot plugin marketplace add <source>, then copilot plugin install <provider>@<marketplace>.
Register plugin-declared MCP server commands in this host's MCP configuration as
the generated note directs. Registration and a dependency declaration alone do
not demonstrate that browser/server tools are callable by the selected worker.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Coordinator MCP allowances use <declared-server>/* for only the package's named
servers. This requires actual server registration and tool discovery; it grants
no undeclared server and does not prove MCP is callable in an installed run.
Schema reference: https://docs.github.com/en/copilot/reference/custom-agents-configuration

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

# Data Feed: Functions, Depth, and Data Quality

The `copy_rates_*` and `copy_ticks_*` family pulls bars and ticks from the MT5 terminal's local cache (downloaded from the broker on demand). All return numpy structured arrays. No rate limits in the local IPC - the bottleneck is the broker download for data not yet cached.

## When to use

Pulling historical OHLCV or ticks for backtesting, indicator computation, or as the bootstrap step of a live data feed. For market depth (Level 2) and live tick subscription (which is also polling), see the bottom of this file.

## Function choice (the only thing to memorize)

| Function | Selects by | Use case |
|----------|-----------|----------|
| `copy_rates_from_pos(symbol, tf, start_pos, count)` | Relative index (0 = current) | Live trading: "last 200 bars" |
| `copy_rates_from(symbol, tf, date_from, count)` | N bars going back from a date | Fixed-size historical windows |
| `copy_rates_range(symbol, tf, date_from, date_to)` | All bars in a calendar interval | Bulk historical download (variable N) |

Tick equivalents: `copy_ticks_from()` and `copy_ticks_range()`. Tick flags: `COPY_TICKS_ALL`, `COPY_TICKS_INFO` (bid/ask only), `COPY_TICKS_TRADE` (last/volume only).

Returned numpy fields: bars = `time, open, high, low, close, tick_volume, spread, real_volume`; ticks = `time, bid, ask, last, volume, time_msc, flags, volume_real`.

## Gotchas

- **MT5 is UTC internally. Naive datetimes silently break things.** The single most common cause of missing/wrong data:
  ```python
  import pytz
  utc = pytz.timezone("Etc/UTC")
  dt = datetime(2024, 1, 1, tzinfo=utc)   # always tz-aware UTC
  ```
- **`real_volume` is always 0 for OTC forex.** Only exchange-traded instruments populate it. Use `tick_volume` for forex (counts ticks, not contracts) and never benchmark forex liquidity by `real_volume`.
- **`tick_volume` varies between brokers** for the same instrument. ECN brokers report more ticks; market makers may filter/aggregate. Don't assume cross-broker comparability.
- **`spread` field = spread at bar close**, not the average. Useful as a sanity gauge, useless as a trading signal on its own.
- **Tick depth is broker-dependent**: from a few days to 1-2 years. EURUSD generates ~200k+ ticks/day - requesting months produces tens of millions of rows. Cache aggressively.
- **"Max bars in chart" defaults to 100,000.** Set to **Unlimited** in MT5 → Tools → Options → Charts, otherwise large historical pulls return truncated arrays with no error.
- **MT5 builds intraday timeframes from M1.** No M1 cache = no derived intraday data. Weekends/holidays have no bars (no placeholder rows inserted).
- **Tick data quality matters more than bar data.** ECN brokers ≫ market makers for tick fidelity. If you're tick-driven, broker selection is part of your strategy.
- **`market_book_*` (Level 2) is also polling** - there are no push notifications for depth updates either.

## Bootstrap + incremental cache (the production pattern)

Parquet with Zstandard compression is the community choice - ~5-10x compression, type preservation, fast reads via pandas/pyarrow. Tick data: partition by day or month.

```python
import pandas as pd

# Initial bootstrap
rates = mt5.copy_rates_range("EURUSD", mt5.TIMEFRAME_M1, start, end)
df = pd.DataFrame(rates)
df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
df.to_parquet("eurusd_m1.parquet", compression="zstd")

# Incremental update (every run after bootstrap)
existing = pd.read_parquet("eurusd_m1.parquet")
last_time = existing['time'].max()
new_rates = mt5.copy_rates_from("EURUSD", mt5.TIMEFRAME_M1, last_time, 10000)
if new_rates is not None and len(new_rates) > 0:
    new_df = pd.DataFrame(new_rates)
    new_df['time'] = pd.to_datetime(new_df['time'], unit='s', utc=True)
    combined = (pd.concat([existing, new_df])
                  .drop_duplicates(subset='time')
                  .sort_values('time'))
    combined.to_parquet("eurusd_m1.parquet", compression="zstd")
```

## Market depth (Level 2)

```python
mt5.market_book_add("EURUSD")
book = mt5.market_book_get("EURUSD")
if book:
    for entry in book:
        side = 'BUY' if entry.type == 1 else 'SELL'
        print(f"{side} {entry.volume} @ {entry.price}")
mt5.market_book_release("EURUSD")
```

Polling-based; you call `market_book_get()` repeatedly to detect changes.

## Typical depth available (broker-dependent)

| Timeframe | Typical depth |
|-----------|---------------|
| D1 | 20-30+ years |
| H1 | 10-15+ years |
| M1 | Weeks to ~2 years |
| Ticks | Days to 1-2 years |

## MT5 vs IBKR for data (one-line summary)

MT5 has no rate limits and includes data with the account, but quality is broker-dependent. IBKR has strict pacing and per-exchange paid subscriptions for most instruments (spot FX is an exception and needs no subscription), but data is exchange-sourced and consistent. Forex/CFD = MT5 wins on convenience; equity/futures with real volume = IBKR wins on quality. One IBKR-specific trap has no MT5 equivalent: its historical responses include the currently-forming bar as the last row, and its FX responses carry session-anchored stub bars, so code ported from MT5 must drop both.

## Official docs

- `copy_rates_*` reference: https://www.mql5.com/en/docs/python_metatrader5/mt5copyratesfrom_py (and `_pos`, `_range`)
- `copy_ticks_*` reference: https://www.mql5.com/en/docs/python_metatrader5/mt5copyticksfrom_py
- `market_book_*` (Level 2): https://www.mql5.com/en/docs/python_metatrader5/mt5marketbookadd_py
- Symbol info: https://www.mql5.com/en/docs/python_metatrader5/mt5symbolinfo_py
- Parquet + Zstd (PyArrow): https://arrow.apache.org/docs/python/parquet.html

## Related

- `api-architecture.md` - the constraints behind "no rate limits" / "no callbacks"
- `event-system-polling.md` - polling loops that consume this data live
- `order-execution.md` - using `symbol_info_tick()` before placing orders
