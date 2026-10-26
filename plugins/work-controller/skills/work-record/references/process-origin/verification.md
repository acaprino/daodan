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
