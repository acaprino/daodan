---
name: investigation-method
description: >
  Investigate an observed error, bug or strange behavior to a demonstrated cause, without fixing it: facts, perimeter from the map, isolated hypotheses, a reproduction test, bisection.
  TRIGGER WHEN: the user reports an error, regression or strange behavior whose cause is unknown and wants it investigated, a coordinator investigates a problem, or a bug fix starts without a known cause.
  DO NOT TRIGGER WHEN: assessing a change or artifact for defects (use review-method), or the root cause is already established with evidence.
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

# Investigation

Trace an observed defect to its causal code/change; never edit product code.
Load `work-controller:work-record`: operation `investigate`, writing only inside
the run and the reproduction test.

## 1. Facts

From the failing environment (run's `environment`), collect exact message,
stack trace, logs/durations, triggering input/steps and last known good
commit/release/date. Read available logs first; otherwise a local rerun counts
only with the same symptom. Repeated round durations (30.0x s) suggest a
configured timeout; record its location. Ask for missing facts one question at
a time, or record them with work-record's `ask` and close the turn. Mark facts
`observed` (user, log, run) or `derived`.

## 2. Perimeter

From the stack and the named symbols, load `codebase-map:map-method`, locate
the symbols through its `references/locate.md` (`codebase_map_search` or
`snapshot.py search` with the names in the report and the traceback frames;
exact symbol and traceback matches rank first), then take `snapshot.py
edit-impact` for each. The suspects are the commits that touched
the perimeter after the last known good
(`git log --format='%h %an %ad %s' GOOD..HEAD -- PATHS`), or its last twenty
without one. Without a map, a recorded gap, the perimeter comes from the stack
and a search.

## 3. Hypotheses

At most three, each with its mechanism (how this code produces the observed
fact), trigger, refuting counterevidence, suspect commit and evidence class.
Each goes to one isolated verifier, blind to the others, with only the facts,
the perimeter and its own hypothesis:

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
`file:line` chain from trigger to symptom, `REFUTED` with the contradicting
`file:line`, or `UNCERTAIN` with what would settle it. A sharper hypothesis it
proposes gets one more round, two at most.

## 4. Reproduction

For the strongest surviving hypothesis, dispatch `testing:test-writer` for one
minimal test that fails on the current code for the reason the hypothesis
states, with the observed symptom (message, exception, timeout bound) at the
data volume that decides it. A different failure on smaller or cached data is
a second defect, not the reproduction. It sits where the fix will keep it,
uncommitted and recorded in the run. With a suspect commit, it must pass on its parent,
checked in a disposable worktree under the run. Without one the cause stays a
hypothesis.

## 5. Bisection and runtime evidence

With a last known good and no confirmed suspect, run `git bisect run` with
the reproduction test in a disposable worktree under the run, never in the
user's checkout. Execute only there or through the project's own runner: most
verbose logging, temporary tracing, a test repeated a hundred times for a
suspected race. No interactive debugger. Record every command with its output.

## 6. Verdict

Write `investigation.md` in the run: facts, perimeter, each hypothesis with
its verdict and evidence, the reproduction test with its failing output, the
first bad commit, and one conclusion. `demonstrated`: confirmed and
reproduced. `probable`: confirmed, not reproduced. `open`: the surviving
hypotheses and what would decide each. Never a fix: a correction goes through
the task cycle, with the reproduction test as its oracle.
