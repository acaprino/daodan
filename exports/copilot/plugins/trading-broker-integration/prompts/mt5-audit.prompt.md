---
name: mt5-audit
description: 'Report on the reliability, error handling, and production readiness of an existing system. TRIGGER WHEN: the user asks to review, audit, or validate an MT5 Python trading bot (polling loops, fill modes, reconnection, order retcodes, Windows deployment). DO NOT TRIGGER WHEN: building from scratch (use the mt5-architect agent), or auditing an IB system (use /trading-broker-integration:ibkr-audit).'
argument-hint: '[path-or-description]'
---

> Arguments: `[path-or-description]`. Wherever `<arguments>` appears below, substitute the text the user typed after the prompt name.

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

<!-- Generated by the Daodan compiler for copilot. Edit the kernel, never this file. -->

# MT5 Trading System Audit

Analyze an existing MT5 Python trading system and produce an actionable audit report.

## Instructions

1. **Identify MT5 components** in the codebase:
   - Connection setup (initialize, login, server)
   - Event/polling loop structure
   - Order execution logic
   - Data fetching approach
   - Error handling
   - Reconnection handling
   - Logging

2. **Audit each component** against best practices:

### Connection
- [ ] initialize() called once at startup (not in loops)
- [ ] shutdown() called once at exit
- [ ] All required params: path, login, server, password, timeout
- [ ] /portable flag used if installed in Program Files
- [ ] Single process per MT5 terminal instance

### Event System
- [ ] Polling loop implemented (not missing events)
- [ ] New candle detection via time field comparison
- [ ] Position change detection via ticket set comparison
- [ ] Appropriate poll interval for strategy timeframe
- [ ] Not using time.sleep() excessively (CPU waste)

### Order Execution
- [ ] Fill mode detected dynamically per symbol (not hardcoded)
- [ ] order_check() called before every order_send()
- [ ] All retcodes handled (especially 10030 invalid fill, 10016 invalid stops)
- [ ] Position ticket specified when closing in hedging mode
- [ ] Magic number used (non-zero) for all bot orders
- [ ] Server-side SL/TP set on every position
- [ ] symbol_select() called before trading operations
- [ ] Broker-specific values queried at runtime (stops_level, filling_mode, etc.)

### Data
- [ ] UTC timezone used for all datetime objects (pytz)
- [ ] "Max bars in chart" set to Unlimited in terminal
- [ ] Data cached locally for efficiency (Parquet recommended)
- [ ] Incremental updates (not full re-download each run)

### Error Handling
- [ ] Every API call checked for None return
- [ ] last_error() called on failures for diagnostics
- [ ] IPC errors handled (-10001, -10002, -10003, -10005)
- [ ] Retcode 10004 (requote) triggers price refresh + retry
- [ ] Retcode 10024 (too many requests) triggers backoff
- [ ] Silent error pattern avoided (no unchecked returns)

### Thread Safety
- [ ] All MT5 calls on single thread
- [ ] asyncio used for concurrency (not threading)
- [ ] No concurrent access to IPC pipe
- [ ] Multi-account uses separate processes

### Reconnection
- [ ] terminal_info().connected checked periodically (health check)
- [ ] Exponential backoff reconnection implemented
- [ ] psutil used to monitor terminal64.exe process
- [ ] subprocess.Popen for terminal restart capability
- [ ] MT5 auto-updates disabled during trading hours
- [ ] Weekend handling implemented (sleep mode)

### Production Hardening
- [ ] Structured logging with rotation
- [ ] Circuit breaker (stop after N consecutive errors)
- [ ] Kill switch (flatten all positions and halt)
- [ ] Process auto-restart (Task Scheduler or watchdog)
- [ ] Demo vs live behavior differences accounted for
- [ ] State reconciliation on restart (positions, orders)

3. **Generate report** with:
   - Current state assessment (what is implemented correctly)
   - Risk areas (missing or misconfigured components)
   - Priority improvements ordered by production impact
   - Code examples for each recommendation
