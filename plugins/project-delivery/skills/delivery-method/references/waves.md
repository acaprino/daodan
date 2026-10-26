# Phases 4 and 5: plan and execution

## Compile the plan

Load `references/specification.md`; verify the specification binding when present.
Translate approved requirements and decisions into waves. Each task carries `id`,
`write_set`, `oracle` (command and expected pre-change failure), `verification`,
`resource_locks`, `produces`, `consumes` (`question:<id>` waits for an answer),
`EX-*` and `INV-*`. Cite the specification path, SHA-256 and approval source.
Pure repair/refactor and legacy runs without a specification retain their method.
Use provider I1 per `references/context-cycle.md`; approved contracts determine
precedence. Build missing oracle fixtures first.

Write `waves`. The helper refuses unjustified write sets over four files,
overlapping files/locks/contracts within a wave, parallelism outside `WORKTREE`
and missing oracles. Correct rejected plans; refusal writes nothing.

## Review of the plan (stage B)

Run `senior-review:review-method`, shape `light`, kind `plan`, stage `plan`:
falsify cited paths, symbols, callers and oracle failures. Record `plan_candidate`
and PASS `plan_review` before tasks run. After three unsuccessful rounds, ask.
Show the plan and cost; obtain approval unless execution is already authorized.

## Execute a wave

New process-backed runs admit and bind the approved graph and worker outputs
through `work-controller:work-record`'s `references/process-runtime.md` before
dispatch. Use its ready packet/attempt; admit artifacts before native delivery.
Reviews retain their ledger. Process success replaces no domain gate or grant;
omit engine commit jobs. Verify the specification binding before execution.

For each task, parallel only in `WORKTREE`:

1. Capture `pre_phase_sha` and pre-step bytes of every owned file.
2. Verify `task-packet` per `references/context-cycle.md`. Brief through
   `references/worker-brief.md`; dispatch `python-development:python-engineer`,
   dispatch `typescript-development:typescript-engineer`, `testing:test-writer` for tests,
   otherwise the isolated worker. Load `skill-catalog:skill-catalog` for knowledge.
   Run the oracle first: unexpected success/failure is `ORACLE_INVALID`. Stay in
   `write_set`, else `NEEDS_REPLAN`; verify and return paths plus uncovered rulings.
3. On `OK`, confirm paths, rerun verification and snapshot the candidate.
   Record PASS `verification_receipt` with digest and HEAD.
4. Run `senior-review:review-method`, shape `light`, kind `changeset`, stage
   `pre-commit-<task id>`. Record roster and `pre_commit_review`. BLOCK, missing
   evidence or edits prevent commit; edits require fresh verification and review.
5. With PASS and commit authorization, stage owned paths and commit atomically:
   `<type>(<area>): <task title>`, trailer `Daodan-Task: <run id> wave <n>/<m>`.
   Record `commit_sha`; HEAD and scoped bytes must match the reviewed candidate.
   Otherwise retain uncommitted. After interruption inspect HEAD/bytes; never
   retry blindly or assume `HEAD~1`.
6. Refresh map/protocol and prepare `post-task`. On failure restore only captured
   owned bytes, remove task-created files and preserve other work. `NEEDS_REPLAN`
   returns to planning; `ORACLE_INVALID` to specification/test.

## Review of the wave (stage C)

Review every completed wave through `senior-review:review-method`, shape `light`,
stage `wave-<n>`, using `EX-*`, `INV-*` and rulings. Record PASS `wave_review`
on its exact digest/HEAD. BLOCK reopens the task. Seal only after every task
is committed and reviewed. Requested readability edits through
`clean-code:readability-method` require a new planned, verified and reviewed task.
