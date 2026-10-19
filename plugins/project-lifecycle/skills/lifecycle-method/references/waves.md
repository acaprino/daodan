# Phases 4 and 5: plan and execution

## Compile the plan

Translate the record into micro-tasks and group them into waves. Every task
carries `id`, `write_set`, `oracle` (command and the failure it must produce
before the change), `verification` command, and when relevant
`resource_locks`, `produces`, `consumes`, the `EX-*` it makes pass and the
`INV-*` it enforces. Order callees before callers along the map's resolved
edges. The first wave builds missing fixtures or harnesses when the oracles
need them.

Run the protocol helper's `plan-check` on the draft. It refuses more than
four files in a `write_set` without a reasoned exception, two tasks of one
wave that share a file, a lock or a produced-consumed contract, a parallel
wave outside a `WORKTREE` workspace, and a missing oracle. Correct the plan
until it passes, then write it into the run's `waves` section.

## Review of the plan (stage B)

Run `senior-review:review-method` with `target-kind=plan` and budget `delta`
on the plan. The preparation selects the premise lens (every cited path,
symbol and caller exists in the current tree), the test lens (every oracle
fails for the right reason and cannot pass trivially), the initialization
lens (ordering, hidden shared files, migrations), the abstraction lens (no
second owner for an existing concept) and the stack lenses of the named
files. Up to three planner-and-lenses rounds, then the user. Present the
approved plan with its expected cost and stop for approval, unless the
authorization already covers execution.

## Execute a wave

For each task, in the order the wave fixes (parallel only in a `WORKTREE`):

1. Record `pre_phase_sha` and the pre-step bytes of every `write_set` file
   through the protocol helper.
2. Dispatch the writer with the brief of `references/worker-brief.md`:
   `python-development:python-engineer` for Python,
   `typescript-development:typescript-engineer` for TypeScript and
   JavaScript, `testing:test-writer` for a task that writes tests only, the
   isolated worker with the knowledge `skill-catalog:skill-catalog` selected
   for any other stack. The writer runs the oracle first and stops with
   `ORACLE_INVALID` when it passes or fails for another reason; writes only
   inside `write_set` and stops with `NEEDS_REPLAN` when another file must
   change; runs the verification; records a ruling for any local decision the
   record did not make; returns `OK` with the changed paths.
3. On `OK`, confirm that the changed paths are a subset of `write_set`, run
   the verification again in this context, and commit atomically when
   authorized (otherwise record the candidate snapshot). On any other code,
   restore the task's `write_set` from the pre-step bytes, remove files the
   task created, leave everything else untouched, and record the attempt.
   `NEEDS_REPLAN` returns to the plan with the missing file; `ORACLE_INVALID`
   returns to the record or the test.

## Review of the wave (stage C)

When every task of the wave is committed or its candidate is recorded, run
`senior-review:review-method` with budget `delta` on the wave's diff. The
preparation selects the logic lens for conformance to `EX-*` and `INV-*`, the
test lens for the new oracles, the premise lens on every new ruling, and the
stack lenses the diff activates. A blocking finding reopens the task; the
wave is `sealed` only with every task committed and the review delivered.
Then the next wave.

`clean-code:readability-method` may run once per wave on the wave's files,
after the review and with the oracles green, when the user asked for it.
