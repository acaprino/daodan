---
name: investigation-method
description: >
  Investigate an observed error, bug or strange behavior to a demonstrated cause, without fixing it: facts, perimeter from the map, isolated hypotheses, a reproduction test, bisection.
  TRIGGER WHEN: the user reports an error, regression or strange behavior whose cause is unknown and wants it investigated, a coordinator investigates a problem, or a bug fix starts without a known cause.
  DO NOT TRIGGER WHEN: assessing a change or artifact for defects (use review-method), or the root cause is already established with evidence.
---

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

# Investigation

The review engine run in reverse. A review looks for defects in a change; an
investigation starts from an observed defect and looks for the code and the
change that cause it. It never edits product code. Load
`project-protocol:project-protocol`: the investigation is a run with
operation `investigate`, and everything it writes stays under that run except
the reproduction test.

## 1. Facts

Collect the exact message, stack trace and logs, the input or steps that
trigger it, the environment (the run's `environment`), and since when: the
last known good commit, release or date. Ask for what is missing one question
at a time with the host's question tool, or record it in the run's
`questions` and close the turn. Mark each fact `observed` (the user, a log, a
run) or `derived`.

Read the failing environment's own evidence before any hypothesis: the log of
the failing request where it failed, not a local rerun. Durations that cluster
at a round value (30.0x s on every attempt) point to a configured timeout;
record the value and where it is set. Evidence you cannot reach (an expired
credential, no log access) is an open fact to obtain, never a reason to
proceed from a local reproduction instead.

## 2. Perimeter

From the stack and the named symbols, load `codebase-map:map-method` and take
`snapshot.py edit-impact` for each: callers, callees, digests, cards, recent
changes. The suspects are the commits that touched the perimeter after the
last known good (`git log --format='%h %an %ad %s' GOOD..HEAD -- PATHS`), or
its last twenty without one. A missing map is a recorded gap; the perimeter
then comes from the stack and a search.

## 3. Hypotheses

At most three, each with its mechanism (how this code produces the observed
fact), trigger, the counterevidence that would refute it, the suspect commit
and the evidence class. Each goes to one verifier in an isolated context,
blind to the other hypotheses, with the facts, the perimeter and its own
hypothesis only:

| Mechanism | Verifier |
|---|---|
| Timers, retries, scheduling, clocks | `senior-review:temporal-resilience-auditor` |
| Persistence, transactions, caches | `senior-review:data-integrity-auditor` |
| Statement cost, data volume, timeouts | `senior-review:sql-efficiency-auditor` |
| Initialization order, startup | `senior-review:chicken-egg-detector` |
| UI timing, layout, focus, scroll | `senior-review:ui-race-auditor` |
| Handles, connections, locks, threads | `senior-review:resource-lifecycle-auditor` |
| Calls and messages across services | `senior-review:distributed-flow-auditor` |
| State, ordering, invariants | `senior-review:logic-integrity-auditor` |
| Anything else | `senior-review:code-auditor` |

The verifier's mandate is the hypothesis, not a hunt: `CONFIRMED` with the
`file:line` chain from trigger to symptom, `REFUTED` with the `file:line` that
contradicts it, or `UNCERTAIN` with what would settle it. A sharper hypothesis
it proposes enters one more round; two rounds at most.

## 4. Reproduction

For the strongest surviving hypothesis, dispatch `testing:test-writer` for one
minimal test that fails on the current code for the reason the hypothesis
states. It sits where the fix will keep it, uncommitted and recorded in the
run as the one project file an investigation writes. With a suspect commit,
the test must pass on its parent, checked in a disposable worktree under the
run. Without a reproduction the cause stays a hypothesis, and the report says
so.

The reproduction must show the observed symptom: the same message or exception
type and, for a timeout, the same bound, with the data volume and storage state
that decide it (a dataset that fits in memory hides disk-bound cost). A
different failure on a smaller or cached dataset is a second defect, recorded
as such; it does not reproduce the first. One defect can hide another: a
statement cancelled by a timeout never reaches its end-of-statement constraint
checks.

## 5. Bisection and runtime evidence

With a last known good and no confirmed suspect, run `git bisect run` with
the reproduction test in a disposable worktree under the run, never in the
user's checkout. Execution happens only there or through the project's own
runner and interpreter: the program with its most verbose logging, temporary
tracing, a test repeated a hundred times for a suspected race. No interactive
debugger. Record every command with its output.

## 6. Verdict

Write `investigation.md` in the run: facts, perimeter, each hypothesis with
its verdict and evidence, the reproduction test with its failing output, the
first bad commit, and one conclusion. `demonstrated`: a confirmed hypothesis
and a failing reproduction. `probable`: confirmed, not reproduced. `open`: the
surviving hypotheses and what would decide each. Never a fix: a correction
goes through the task cycle, with the reproduction test as its oracle.
