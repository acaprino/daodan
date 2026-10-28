# Plan: lock-free work ownership, stage 1

Date: 2026-10-28. Status: **proposed plan; execution not authorized**.

## 1. Binding

- Specification: [lock-free work ownership](2026-10-28-lock-free-work-ownership-design.md),
  revision 4, SHA-256 `2a8e1eb8a47baa15ed7de97ec43e210543a0b17e463621dde85ebad0a60d603d`,
  approved by the user on 2026-10-28 ("Approvo"). Work record
  `.daodan/runs/lock-free-ownership-20261028/`, whose `intent.md` binds that
  digest and answer.
- The user's "vai" authorizes this plan only. Approving it grants no code,
  commit, merge or push; those are asked separately before execution.
- Scope: stage 1 (spec S-1, S-3, S-4, S-5 and their documentation). Stage 2
  (S-6 to S-8) gets its own plan after stage 1 is integrated, because its
  agenda join reads the `last_activity` that stage 1 writes.
- Base: `5cf722b54` (HEAD when planned). The uncommitted workspace reservation
  work in the main checkout stays untouched (UD-5).

## 2. Execution setting

- Workspace `WORKTREE`, created at preflight through `worktree-manager` from the
  base above, under `.daodan/worktrees/`. All work, tests and commits happen
  there; the main checkout is not edited.
- Waves run their tasks **sequentially** (`parallel: false`): tasks are small,
  sequential runs keep the machine light, and a later switch to parallel would
  need a new plan review.
- Execution binds a process graph before dispatch, as
  `work-record/references/process-runtime.md` requires for new execution runs.
- Each task: the worker writes the new test first and runs the oracle (it must
  fail as stated), implements, runs the verification; then a light pre-commit
  review of the changeset; then one atomic commit with trailer
  `Daodan-Task: lock-free-ownership-20261028 wave <n>/6`. Each wave closes with a
  light wave review.
- Implementers: `python-development:python-engineer` for code tasks,
  `work-controller:isolated-worker` for documentation tasks.
- Versions stay at 1.0.0 (owner rule of 2026-10-28). `check_version_bumps.py`
  will flag the range; that result is reported, not silenced.

## 3. Ruling

- RU-1: S-5 names the sidecar rule `<old lock name>.oslock` and, in the same
  bullet, `.retention.oslock`. The plan applies the rule:
  `.retention.lock.oslock` joins `CONTROL`. Cost if wrong: one renamed constant.

## 4. Waves

Shared columns: every task consumes `spec:2a8e1eb8`. `INV-2` and `INV-5` are
checked by the existing suites the verification runs.

### Wave 1: the lock primitive

| Task | Write set | Oracle (fails before the change) | Verification | Covers |
|---|---|---|---|---|
| T1 `oslock` primitive | `plugins/codebase-map/skills/map-method/scripts/oslock.py`, `tests/test_oslock.py` | `python -m unittest tests.test_oslock`: fails with `ModuleNotFoundError: No module named 'oslock'` | same command passes: sidecar lock serializes two processes; a holder killed with `kill`/`TerminateProcess` releases it; a leftover old-name file never blocks; `directory_lock` creates no file in the directory; contention past the deadline raises the retry error; every `plugins/*/skills/*/scripts/oslock.py` is byte-identical to this one | INV-3, INV-4 |

`oslock.py` offers `sidecar_lock(path, timeout)` (one byte at offset 0;
`msvcrt.locking(LK_NBLCK)` / `fcntl.flock`; touches mtime on acquire; probe
helper `held(path)` that never creates the sidecar) and
`directory_lock(directory, timeout)` (Windows named mutex keyed by the SHA-256
of the `normcase` canonical path; `fcntl.flock` on the directory descriptor),
plus `replace_with_retry(source, target)` for Windows `PermissionError`.
Produces `oslock-primitive`.

### Wave 2: every file-existence lock becomes an OS lock

All tasks consume `oslock-primitive`. T4 to T7 copy `oslock.py` byte for byte.

| Task | Write set | Oracle | Verification | Covers |
|---|---|---|---|---|
| T2 retrieval lock and contract | `codebase-map/.../scripts/retrieval.py`, `tests/test_codebase_map_retrieval.py`, `tests/test_codebase_map_index_cli.py`, `tests/test_codebase_map_mcp.py` | new test "a leftover `<index>.lock` from a killed build does not block `ensure_index`" fails with the current lock-held error | `python -m unittest tests.test_codebase_map_retrieval tests.test_codebase_map_index_cli tests.test_codebase_map_mcp` passes; `lock`/`lock_age_s` reported only while held; `break_lock` sweeps temporaries under the lock, also on a fresh index | INV-3, INV-4 |
| T3 semantic map and embeddings | `codebase-map/.../scripts/semantic_map.py`, `.../embedding_worker.py`, `tests/test_codebase_map_semantic_map.py`, `tests/test_codebase_map_embeddings.py` | new tests "leftover lock file does not block" fail with `FileExistsError` | `python -m unittest tests.test_codebase_map_semantic_map tests.test_codebase_map_embeddings` passes | INV-3, INV-4 |
| T4 worktree catalog | `worktree-manager/.../scripts/oslock.py`, `.../workspaces.py`, `tests/test_worktree_catalog.py` | new test "a leftover `.worktrees.lock` does not make `annotate` fail with `catalog_busy`" fails | `python -m unittest tests.test_worktree_catalog tests.test_worktree_recovery tests.test_oslock` passes; the `catalog_busy` stale-lock test (`:396-401`) now asserts the opposite | INV-3, INV-4 |
| T5 ADR directory lock | `project-delivery/skills/adr-method/scripts/oslock.py`, `.../adr_tool.py`, `tests/test_adr_method.py` | EX-6 test (killed writer leaves a temporary; next write succeeds; `git status` shows only the record) fails with `.adr-lock is held` | `python -m unittest tests.test_adr_method tests.test_oslock` passes; temporaries older than one hour are swept; docstring `adr_tool.py:35-36` updated | EX-6, INV-3, INV-4 |
| T6 FRD directory lock | `project-delivery/skills/frd-method/scripts/oslock.py`, `.../frd_tool.py`, `.../frd-method/references/frd-schema.md`, `tests/test_frd_method.py` | same shape as EX-6 for FRD fails with `.frd-lock is held` | `python -m unittest tests.test_frd_method tests.test_oslock` passes; `frd-schema.md:123` and `frd_tool.py:20-21` updated | INV-3, INV-4 |
| T7 retention lock | `project-delivery/skills/delivery-method/scripts/oslock.py`, `.../artifacts.py`, `tests/test_lifecycle_artifacts.py` | new test "a leftover `.retention.lock` does not refuse retention" fails with `Retention is locked` | `python -m unittest tests.test_lifecycle_artifacts tests.test_oslock` passes; `.retention.lock.oslock` in `CONTROL` (RU-1) | INV-3, INV-4 |

### Wave 3: work records and tickets

| Task | Write set | Oracle | Verification | Covers |
|---|---|---|---|---|
| T8 agenda without a session lock | `work-controller/.../scripts/run_state.py`, `tests/test_work_record.py`, `tests/test_worktree_recovery.py` | EX-1 test (B resumes a task A held) fails with `is held by session`; EX-4 and EX-5 fail the same way | `python -m unittest tests.test_work_record tests.test_worktree_recovery` passes: EX-1 to EX-5; `holder` always `null`; `last_activity` written; `--take-over` accepted with or without `--session`; `recent_activity` under 15 minutes; `atomic_write` retries `PermissionError` | EX-1 to EX-5, INV-1, INV-6 |
| T9 tickets | `work-controller/.../work_controller/store.py`, `tests/test_work_controller_decisions.py` | EX-7 test (B claims and closes K after A) fails with `ticket is not at the open frontier or is already held` | `python -m unittest tests.test_work_controller_decisions tests.test_work_controller_regressions` passes; `ticket.reassigned` IDs unique; `map_status` lists tickets in progress | EX-7, INV-1 |

### Wave 4: process attempts

| Task | Write set | Oracle | Verification | Covers |
|---|---|---|---|---|
| T10 blocking attempts reported | `work-controller/.../work_controller/store.py`, `.../engine.py`, `.../cli.py`, `tests/test_work_controller_regressions.py` | EX-8 test fails with `KeyError: 'blocking_attempts'` | `python -m unittest tests.test_work_controller_regressions tests.test_work_controller_engine tests.test_work_controller_cli tests.test_work_controller_mcp` passes; `frontier` output unchanged | EX-8, INV-1 |

### Wave 5: documentation

| Task | Write set | Oracle | Verification |
|---|---|---|---|
| T11 work-controller bodies | `work-record/SKILL.md`, `work-record/references/process-runtime.md` | `rg -n -- "--take-over\|Only holders write\|Writes also require" plugins/work-controller --type md` finds lines | the same search finds nothing; process-runtime.md names `blocking_attempts` and the `resume` recovery |
| T12 delivery bodies, part 1 | `delivery-method/references/continue.md`, `finish.md`, `preflight.md`, `status.md` | `rg -n "holder\|take-over" ` on those four files finds lines | the same search finds only `last_activity` wording |
| T13 delivery and worktree bodies | `delivery-method/references/retention.md`, `sync.md`, `worktree-method/SKILL.md`, `worktree-method/references/lifecycle.md` | `rg -n "holder\|live session's lock\|no active session"` on those files finds lines | the same search finds nothing |
| T14 entry and instructions | `plugins/daodan/workflows/show-status.md`, `CLAUDE.md` | `rg -n "holder" plugins/daodan/workflows/show-status.md CLAUDE.md` finds lines | the same search finds only `last_activity` wording |
| T2b `break_lock` descriptions | `codebase-map/.../scripts/mcp_server.py`, `.../scripts/snapshot.py`, `.../references/mcp.md`, `.../references/locate.md` | `rg -n "break_lock"` on them shows it "removes" the lock | the new wording, and `python -m unittest tests.test_codebase_map_mcp tests.test_codebase_map_index_cli` passes |

### Wave 6: build and gates

| Task | Write set | Oracle | Verification |
|---|---|---|---|
| T15 rebuild | `AGENTS.md`, `docs/catalog.md` and the `docs/plugins/*.md` pages the sync changes (granularity exception: generated output, committed with the kernel by repository rule, as in run `20261027-code-access` task `t7-versions-build`) | `python scripts/daodan_build.py --check --support` reports drift | `python scripts/daodan_build.py`, then `--check --support`, `sync_plugin_docs.py --check`, `sync_codex_instructions.py --check`, the linters of CLAUDE.md "Build / CI" 1 to 4 and 9, `python -m unittest discover -s tests`, and `rg --type md -n -- "--take-over\|held by session" plugins` finding nothing |

## 5. Reviews and cost

- Stage B: this plan gets a light `plan` review before any task runs.
- Per task: one light changeset review before commit. Per wave: one light wave
  review. Total: 16 tasks, about 23 reviews.
- Estimate: 4 to 6 hours of agent time and several million tokens, dominated by
  reviews (each review of this spec used 170 000 to 210 000 tokens).

## 6. Integration

Integration is a separate decision after wave 6: squash (preselected) or full
history into `master`, under the user's merge authorization. The uncommitted
reservation work in the main checkout touches `commit_change` and
`validate_transitions` (spec A-6), so integration happens after its owner
commits or discards it, and resolves that overlap explicitly.
