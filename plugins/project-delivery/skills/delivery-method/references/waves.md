# Phases 4 and 5: plan and execution

## Compile the plan

Translate the record into micro-tasks grouped into waves. Each task carries `id`,
`write_set`, `oracle` (command and expected pre-change failure), `verification`
command, relevant `resource_locks`, `produces`, `consumes` (`question:<id>` waits
for an answer), the `EX-*` it makes pass and `INV-*` it enforces. Use provider I1
per `references/context-cycle.md`; approved contracts determine precedence. Build
missing oracle fixtures first.

Write the draft into `waves`. The helper refuses an unjustified write set over
four files, tasks sharing files, locks or produced-consumed contracts in one wave,
parallelism outside `WORKTREE`, and missing oracles. A refusal writes nothing;
correct the plan until accepted.

## Review of the plan (stage B)

Run `senior-review:review-method`, shape `light`, kind `plan`, stage `plan`, as
an adversarial review: the premise auditor tries to falsify cited paths, symbols,
callers and every oracle's stated failure. Record `plan_candidate` and a
`plan_review` receipt. No task may enter `running` before the review is delivered
with PASS. Use three rounds, then ask. Present the approved plan
and expected cost; stop for approval unless authorization covers execution.

## Execute a wave

For a new process-backed run, admit the approved graph and bind it as
`work-controller:work-record` describes in `references/process-runtime.md`
before dispatch. Graph agent jobs map to declared native worker reports;
review deliveries outside the graph retain their own ledger entries. Use
the bundled controller's ready packet and attempt identity for dispatch,
admit its artifact before recording the corresponding native delivery, and
continue its frontier after admission. It does not replace stages B or C,
authorize a commit, or turn a missing report into a delivery. Omit engine
commit jobs from the bound graph: this method owns reviewed commits.

For each task in wave order, parallel only in a `WORKTREE`:

1. Record `pre_phase_sha` and pre-step bytes of every `write_set` file.
2. Verify `task-packet` per `references/context-cycle.md`; dispatch with
   `references/worker-brief.md`: dispatch `python-development:python-engineer`
   for Python, dispatch `typescript-development:typescript-engineer` for
   TypeScript/JavaScript, dispatch `testing:test-writer` for tests only,
   otherwise the isolated worker; load skill `skill-catalog:skill-catalog` for knowledge. The writer runs the
   oracle first, returning `ORACLE_INVALID` if it passes or fails differently;
   writes only `write_set`, returning `NEEDS_REPLAN` if more files are needed;
   runs verification, records uncovered local rulings and returns `OK` with paths.
3. On `OK`, confirm paths, rerun verification and snapshot the uncommitted
   candidate. Record passing `verification_receipt` with its digest and HEAD.
4. Run `senior-review:review-method`, shape `light`, kind `changeset`, stage
   `pre-commit-<task id>`, on that candidate. Record its roster before dispatch
   and its result as `pre_commit_review`. `BLOCK`, missing evidence or any edit
   prevents commit; edits require fresh snapshot, verification and review.
5. With PASS and commit authorization, stage only owned paths and make one atomic
   commit: `<type>(<area>): <task title>`, trailer `Daodan-Task: <run id> wave <n>/<m>`.
   Record `commit_sha`. The helper accepts committed status only when current
   HEAD is that commit and scoped bytes match the reviewed digest. Without
   authorization, retain the candidate uncommitted. After uncertain interruption,
   inspect HEAD and bytes on resume; never repeat blindly or use `HEAD~1`.
6. At the barrier, refresh map and protocol candidate; prepare `post-task` per
   `references/context-cycle.md`. On other outcomes, restore owned pre-step bytes,
   remove only task-created files and preserve everything else. `NEEDS_REPLAN`
   returns to planning; `ORACLE_INVALID` returns to record or test.

## Review of the wave (stage C)

With every task committed or its candidate recorded, run
`senior-review:review-method`, shape `light`, stage `wave-<n>`, on its diff with
`EX-*`, `INV-*` and rulings as intent. Record the wave candidate and PASS
`wave_review` on the same digest and HEAD. `BLOCK` reopens the task. Seal only
when every task is committed and the wave review is delivered. Then start the
next wave.

Requested `clean-code:readability-method` edits form a new planned task with fresh
verification and pre-commit review; never amend a reviewed candidate silently.
