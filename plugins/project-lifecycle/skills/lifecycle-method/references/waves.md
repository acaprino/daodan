# Phases 4 and 5: plan and execution

## Compile the plan

Translate the record into micro-tasks and group them into waves. Every task
carries `id`, `write_set`, `oracle` (command and the failure it must produce
before the change), `verification` command, and when relevant
`resource_locks`, `produces`, `consumes` (`question:<id>` for an answer it
needs, which holds it until answered), the `EX-*` it makes pass and the
`INV-*` it enforces. Use provider I1 per `references/context-cycle.md`; approved
contracts determine precedence. Build missing oracle fixtures first.

Write the draft into the run's `waves` section. The helper refuses more
than four files in a `write_set` without a reasoned exception, two tasks of
one wave that share a file, a lock or a produced-consumed contract, a parallel
wave outside a `WORKTREE` workspace, and a missing oracle; a refused write
changes nothing. Correct the plan until the write passes.

## Review of the plan (stage B)

Run `senior-review:review-method` with shape `light`, kind `plan` and stage
`plan`: the helper has settled the structure, and the premise auditor checks
every cited path, symbol and caller and that each oracle can fail for its
stated reason. Three planner-and-review rounds at most, then the user. Present the
approved plan with its expected cost and stop for approval, unless the
authorization already covers execution.

## Execute a wave

For each task, in the order the wave fixes (parallel only in a `WORKTREE`):

1. Record `pre_phase_sha` and the pre-step bytes of every `write_set` file
   through the protocol helper.
2. Verify `task-packet` per `references/context-cycle.md`; dispatch with `references/worker-brief.md`:
   for Python dispatch `python-development:python-engineer`,
   for TypeScript and JavaScript dispatch `typescript-development:typescript-engineer`,
   for tests only dispatch `testing:test-writer`, for any
   other stack the isolated worker, with the knowledge selected when you
   load the `skill-catalog:skill-catalog` skill. The writer runs the oracle first and stops with
   `ORACLE_INVALID` when it passes or fails for another reason; writes only
   inside `write_set` and stops with `NEEDS_REPLAN` when another file must
   change; runs the verification; records a ruling for any local decision the
   record did not make; returns `OK` with the changed paths.
3. On `OK`, confirm changed paths are inside `write_set`; rerun verification
   here. Commit atomically when authorized; otherwise snapshot the candidate.
   Use `<type>(<area>): <task title>` with trailer
   `Daodan-Task: <run id> wave <n>/<m>`. At the barrier, refresh the map into a new manifest and the protocol
   candidate; prepare `post-task` per `references/context-cycle.md`.
   On other codes, restore owned pre-step bytes, remove only task-created
   files, preserve everything else and record the attempt. `NEEDS_REPLAN`
   returns missing files to planning; `ORACLE_INVALID` returns to record or test.

## Review of the wave (stage C)

With every task committed or its candidate recorded, run
`senior-review:review-method` with shape `light` and stage `wave-<n>` on the
wave's diff: the project's tools, then the generalist, with the record's
`EX-*` and `INV-*` and the wave's rulings as its intent. A `BLOCK` reopens the task; the
wave is `sealed` only with every task committed and the review delivered.
Then the next wave.

`clean-code:readability-method` may run once per wave, after the review
with the oracles green, when the user asked.
