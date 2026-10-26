<daodan_host_binding host="claude">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Claude binding: repository tools are Read/Glob/Grep and Write/Edit; shell execution
uses Bash and network fetch uses WebFetch. Pass the executable string in Bash's
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

# Verification

Verification date: 2026-10-25. Scope: the initial local vertical slice in this repository.

## Executed checks

| Check | Result |
|---|---|
| Isolated environment | `uv sync` completed with PyYAML 6.0.3 |
| Unit and behavioral suite | 100 tests passed with `uv run python -B -m unittest discover -s tests -v` |
| Python compatibility | The same behavioral suite passes on CPython 3.11 and 3.14.8 |
| Static checks | `uv run --with ruff ruff check src tests`: all checks passed |
| Byte compilation | `uv run python -B -m compileall -q src tests`: passed |
| Package build | Wheel and source distribution built successfully in `dist/` |
| Installed wheel entrypoint | `process-controller --help` succeeded from an isolated `uv run --no-project --with <wheel>` environment |
| Wheel console assets | `console.html`, `console.css` and `console.js` verified present through `importlib.resources` in the isolated wheel environment |
| Public CLI smoke | Two agent jobs completed through `compose`, `start`, `drive`, `start-attempt` and `complete`; the second job read the first job's content-addressed artifact and the run ended `VERIFIED_SUCCESS` |

The final CLI smoke used a disposable workspace under the approved temporary directory. Agent work was simulated by writing the declared artifacts through the public completion contract; no LLM was called.

## Console and MCP

- Eight MCP tests cover legacy initialization, modern discovery, every read-only tool, validation, errors, rate limiting and a real stdio subprocess. The official MCP Inspector is not installed, so no Inspector session was run.
- Twelve web tests cover assets, fragment/sessionStorage authentication, host/method rejection, bounded views and logs, incremental SSE, heartbeat and the four-client limit.
- Four shared-view tests cover bounded metadata, pagination, map dependencies and log tails.
- A real Edge browser rendered the console on desktop and a 390px mobile viewport. It showed runs, jobs, attempts, artifacts, tickets and command output. Pause/resume and stream selection worked. Mobile tables scroll inside their own wrappers without page-level horizontal overflow.
- During the browser session, completing an agent attempt through the public CLI advanced the selected run from 1/2 to 2/2 succeeded and `VERIFIED_SUCCESS` over live SSE. No manual reload was required.
- Two consoles on ports 8891 and 8892 were bootstrapped in the same browser. After the second bootstrap, refreshing the first still returned authenticated data, proving token isolation by origin without authentication cookies.
- The browser demo server was stopped after verification. A different preexisting HTTP server on port 8765 was left untouched.

## Review-driven regressions

An independent source review reported nine findings and two further recovery findings. The implementation now includes sixteen focused regressions covering committed lease revocation, exact-budget success, event namespace isolation, completion side effects, concurrent completion, Git SHA recovery after database and `rev-parse` failures, explicit uncertain-outcome reconciliation, immutable ticket/run binding, failure idempotency, workspace mismatch and supervision after budget exhaustion and many old events.

A further regression verifies that scoped Git commits require the work-tree root. Five additional interface regressions cover cross-port token isolation, workspace-filtered inventories and status, Int64 cursor overflow, excessive query fields and invalid ports. The independent re-review approved those five fixes with the explicit limit of a scoped static review, not a new full audit.

## Evidence boundaries

- No real installed-host agent adapter, host handle, model identity or stop signal was exercised.
- No real Git repository was initialized or mutated. Git behavior was tested with fake runners, including duplicate-commit prevention and recovery after an injected database failure.
- Concurrency tests use local threads and separate SQLite connections. They do not prove production multi-process crash durability, power-loss recovery or distributed execution.
- No benchmark yet establishes a token-saving percentage. Bounded output is a structural property; savings require comparison on equivalent work.
- Dynamic loops, selective replan, parallel execution, LLM composition, per-job model routing and semantic memory are not part of this verified slice.
