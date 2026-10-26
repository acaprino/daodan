# Phase 1: preflight and workspace

Probe; record `workspace`/`preflight`. No product edits.

## Probes

| Probe | Command | Records |
|---|---|---|
| Providers | host plugin inventory | every transitive `daodan` provider active; otherwise stop with host-specific enable/install command |
| Environment | `.venv`, `uv`, `npm`, loop commands | `environment`: interpreter/runners; authorize installation outside project |
| Models | load skill `model-routing:model-routing`, `references/task-routing.md` | `environment.models`: inventory, host support, confirmed per-request assignments |
| Repository/head | `git rev-parse --show-toplevel`, `git rev-parse HEAD` | `base_sha` candidate |
| Working tree | `git status --porcelain=v2 --branch` | staged/unstaged/untracked paths, conflicts (`u` rows), branch |
| Interrupted operation | `MERGE_HEAD`, `rebase-merge` or `rebase-apply` under Git directory | blocks the phase |
| Upstream distance | `git fetch --prune`, then `git rev-list --left-right --count HEAD...@{upstream}` | ahead/behind counts; never blind pull |
| Map context | `codebase-map:map-method`; `references/context-cycle.md` preflight | verify freshness, refresh stale/missing scope; freeze base/packet/I1 before interview |
| Test baseline | project's declared scoped test command | `GREEN`; `KNOWN_RED` with user-accepted failure fingerprint; `UNKNOWN_RED` |
| Migrations | project's declared migration status command | `ALIGNED`, `PENDING`, `DIVERGED`, `UNKNOWN` or `NOT_APPLICABLE` |

Hash failing tests: unchanged known; changed unknown.

## Model binding persistence

Use `model-routing:model-routing` for per-job bindings; pass confirmed assignments
to Work Controller. Its engine cannot call models or discover host identity.
Hardcode no model/host aliases.

Persist confirmed routing at `environment.models.assignments[request_sha256]` through
`work-controller:work-record`: `run_state.py update --project ROOT --run-id ID
--session ID --expected-revision N --payload PATCH.json`. Preserve interpreter/commands/assignments;
reread/merge revision conflicts, revalidate persisted assignments through routing on resume.

## Workspace mode

Load `worktree-manager:worktree-method`; follow creation/reuse/runtime probes.
Honor recorded user/project policy; otherwise new Git-bound tasks use `WORKTREE`.
Reuse requires matching repository/branch/task/holder.

| Mode | Use when | Consequence |
|---|---|---|
| `WORKTREE` | default or selected | main checkout's `.daodan/worktrees/`; task-associated naming; parallel waves allowed |
| `BRANCH` | selected | current checkout, project naming; sequential waves |
| `IN_PLACE` | selected | sequential waves; protect preexisting edits from rollback |

Record task ID/branch/path. Prove host read/write/check access before run
initialization: project paths are immutable. Never nest state homes. Resume
failed setup under existing authorization; do not recreate checkouts or install
global hooks.

Preserve the approved specification's exact bound project-relative path/SHA-256
in the selected checkout; never overwrite foreign work. Verify bytes/approval
through `references/specification.md` before planning.

Missing worktree test files/services: record `path`/`kind`/`secret` (env/schema/fixtures).
Reference secrets; never copy values.

## Special situations

| Situation | Rule |
|---|---|
| Interrupted merge or rebase | Stop; offer resolution first. |
| Behind upstream | Offer rebase/fast-forward or pin `base_sha` and record gap. |
| `UNKNOWN_RED` baseline | Start no feature; offer oracle repair, repair wave first, or `KNOWN_RED` with explicit user acceptance. |
| `PENDING` or `DIVERGED` migrations | Warn before schema tests; bind each worktree's own schema. |
| Dirty `IN_PLACE` | Protect preexisting paths; intersecting `write_set` stops with `NEEDS_REPLAN`. |
| Stale map on the scope | Update incrementally; interview uses fresh map or names stale paths unknown. |

Write `workspace`/`preflight`/`environment`; state mode/base-commit/baseline.
