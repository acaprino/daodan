---
name: investigation-method
description: >
  Investigate an observed error, bug or strange behavior to a demonstrated cause, without fixing it: facts, perimeter from the map, isolated hypotheses, a reproduction test, bisection.
  TRIGGER WHEN: the user reports an error, regression or strange behavior whose cause is unknown and wants it investigated, a coordinator investigates a problem, or a bug fix starts without a known cause.
  DO NOT TRIGGER WHEN: assessing a change or artifact for defects (use review-method), or the root cause is already established with evidence.
---

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
