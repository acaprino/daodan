---
name: ibkr
description: >
  Interactive Brokers integration in Python via TWS API and ib_async, with paper Gateway verification tooling.
  TRIGGER WHEN: building, auditing or debugging TWS / IB Gateway integrations (contracts, market data, orders, brackets, error codes, reconnection, IBC deployment).
  DO NOT TRIGGER WHEN: MetaTrader 5 (use mt5).
---

> `<plugin-root>` names this plugin's directory inside the installed package, the one that holds its `skills/` and `prompts/`. Resolve it once from where this file was loaded, then substitute it into every path below that starts with it.

<daodan_host_binding host="pi">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
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

# Interactive Brokers Integration

Reference for building, operating and debugging systems that trade through the Interactive Brokers TWS
API with `ib_async` in Python. Covers equities, options, futures, FX, CFDs and crypto.

## The one rule this skill is organised around

**IBKR's behaviour is a property of your contract, your account entity and your terminal, not a global
constant.** Most expensive IBKR bugs are not coding errors. They are correct code built on an
assumption about the venue that nobody checked, that was never documented, and that turned out to be
false for that instrument or that account.

So the order of resort, for any question, is:

1. **Read the capability list.** `ContractDetails.orderTypes` declares what that contract accepts.
   Many questions end here, for free.
2. **Read the documentation and quote the sentence.** If you cannot locate it as a sentence on the
   page, you do not have an answer. Never accept a search-engine summary as evidence.
3. **Probe it** against a paper Gateway and keep the transcript.
4. **Record the answer with its provenance and the shapes it covers.**

`venue-questions-and-probes.md` is the doctrine. `gateway-verification.md` is the tooling.

## Quick start

1. **Connection**: IB Gateway (headless, lighter) over TWS. Ports 4002 paper, 4001 live. Offline
   standalone build in production, never the auto-updater.
2. **Library**: `pip install "ib_async<3.0.0"` (Python >= 3.10). The upper bound forces an explicit
   upgrade decision.
3. **Contracts**: qualify, reject `conId <= 0` placeholders, clear the cache on every reconnect.
4. **Prices**: snap to the increment from the **market rule band**, not to `minTick`.
5. **Orders**: value `tif` explicitly on every leg. Treat a returned `placeOrder` as submitted, never
   accepted.
6. **Errors**: subscribe `errorEvent`, `orderStatusEvent`, `openOrder`, and route the library's std
   loggers into your sink. Four channels, all of them load-bearing.
7. **Resilience**: `disconnectedEvent` plus jittered backoff, gated on an active probe rather than on
   `isConnected()`.
8. **Verify**: `scripts/ibkr_gateway.py` provisions a paper Gateway; `scripts/ibkr_probe.py` measures
   what it does.

## Reference materials

**Foundations**
- `tws-api-architecture.md` - protocol, Gateway versus TWS, ports, clientId strategy, session
  exclusivity, `ib_async` setup, pinning and measured divergences, official docs and community
  resources
- `contracts-and-instruments.md` - per-asset-class contract construction, qualification, **market rules
  and the increment actually in force**, size semantics per class, option chains, combos, `whatToShow`,
  and a matrix of which failure modes bite which class

**Orders**
- `order-types-and-attributes.md` - order types, time in force, fill modes and attributes, and how to
  resolve what a given contract accepts instead of guessing
- `bracket-orders.md` - brackets in depth: attached orders plus OCA, transmit staging, TIF per leg,
  OCA types and overfill protection, trigger methods and the stop that never fires, the six variants,
  and the two questions IBKR does not answer
- `order-execution.md` - order lifecycle mechanics, execDetails, race conditions, paper-trading caveats
- `order-lifecycle-contracts.md` - verdict windows, what `placeOrder` returning proves, terminal
  presets, netted close paths, attribution

**Diagnosis**
- `error-codes-and-verdicts.md` - the three layers that can refuse an order, **the `ib_async` grading
  step that cancels live orders locally**, what the published table is and is not, precautions, and how
  to grade a code you have never seen
- `venue-questions-and-probes.md` - the evidence ladder, provenance tags, probe instruments, and the
  standing register of questions the documentation does not answer
- `venue-boundary-failure-modes.md` - the adapter layer: async rejection ingress, tick conformance,
  entity-dependent contract routing, qualification lifecycle, `NaN`-safe sizing, the venue-to-domain
  validation boundary

**Account and data**
- `account-state-and-pnl.md` - the five account surfaces and their cadences, why the two PnL feeds are
  allowed to disagree, `(account, conId)` keying and the absent close event, the current-day execution
  limit under Gateway, **margin and the liquidation that arrives without a margin call**, look-ahead
  risk tags, short-sale availability and the silent locate hold, and Flex as the reconciliation source
- `event-driven-data.md` - subscriptions, bar construction, pacing, historical silence triage,
  session-reopen stub bars, eventkit listener contracts

**Operations**
- `reconnection-resilience.md` - reconnect patterns, the `isConnected()` zombie, half-open connects,
  supervisor self-death, what the terminal preserves, Gateway-log forensics
- `gateway-automation.md` - scheduled outage windows, IBC, multi-process launcher locks, deployment on
  Windows, Linux, macOS and Docker
- `gateway-verification.md` - provisioning a disposable paper Gateway and using it to answer questions

**Data assets**
- `assets/tws-message-codes.tsv` - all 458 published TWS message codes, each tagged with the grade
  `ib_async` assigns it. Search this before inventing a classification.

## Tooling

```bash
S=<plugin-root>/skills/ibkr/scripts

python $S/ibkr_gateway.py doctor              # what is installed, which ports are open
python $S/ibkr_gateway.py install             # download and install Gateway + IBC, unattended
python $S/ibkr_gateway.py configure --user U  # config pinned to paper
python $S/ibkr_gateway.py start               # headless, verified by port probe

python $S/ibkr_probe.py capabilities --stock AAPL       # what this contract really permits
python $S/ibkr_probe.py shape --stock AAPL --type STP --tif GTC --attr allOrNone
python $S/ibkr_probe.py matrix --stock AAPL --types LMT,STP --tifs DAY,GTC,IOC
python $S/ibkr_probe.py bracket --stock AAPL --qty 1    # lifecycle, TIF read-back, preset detection
python $S/ibkr_probe.py codes 10256 10257 10349         # no gateway needed
```

Paper only, enforced twice: live ports are refused, and every managed account must look like a paper
account after connecting.

## Symptoms to entry points

| Symptom | Read |
|---|---|
| Order refused with a code you cannot classify | `error-codes-and-verdicts.md` |
| An order vanished from your books but may be live at the venue | `error-codes-and-verdicts.md`, the grading section |
| Error 110 on a price that looks correct | `contracts-and-instruments.md`, market rules |
| Protective legs expired overnight, or orphaned on a flat position | `bracket-orders.md` |
| A stop that never triggered, with no error | `bracket-orders.md`, trigger methods |
| "Does IBKR support attribute X" | `order-types-and-attributes.md` |
| A position doubled after a close | `order-lifecycle-contracts.md` |
| Orders cancelled moments after submission, code correct | `order-lifecycle-contracts.md`, terminal presets |
| Positions closed by someone other than your strategy | `account-state-and-pnl.md`, liquidation |
| A short order that neither fills nor rejects | `account-state-and-pnl.md`, the locate hold |
| Two PnL numbers that will not reconcile | `account-state-and-pnl.md` |
| Margin or account values that lag reality | `account-state-and-pnl.md`, the three-minute cadence |
| Fills missing after a restart, or older than today | `account-state-and-pnl.md`, executions |
| Handlers that never fire, events that vanish | `event-driven-data.md` |
| Historical bars empty, or corrupting a replay | `event-driven-data.md` |
| Connected-looking but dead for hours | `reconnection-resilience.md` |
| Gateway start collisions, restart loops, outage windows | `gateway-automation.md` |
| A design decision resting on an unverified assumption | `venue-questions-and-probes.md` |

## Key decision points

| Decision | Default | Change when |
|---|---|---|
| Connection target | IB Gateway | Visual debugging wanted: TWS |
| Python library | `ib_async` | Same-day new API features: `ibapi` |
| Live data | `reqRealTimeBars` (5s) | Tick precision: `reqTickByTickData`, capped at 5% of data lines |
| Historical | `reqHistoricalData` + throttle | Bulk backfill: chunked with a semaphore |
| Order price source | Market rule band increment | Never `minTick` alone |
| Bracket children TIF | `GTC` | Strictly intraday systems that guarantee flattening |
| Reconnect backoff | Equal-jitter exponential | Single client on a dedicated Gateway: plain exponential |
| Lifecycle management | IBC + scheduler | Docker available: `gnzsnz/ib-gateway-docker` |
| Capability question | Read `orderTypes` | Token present but still refused: probe with `whatIf` |
