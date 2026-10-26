# Phase 1: preflight and workspace

Probe; record `workspace` and `preflight`.

## Probes

| Probe | Command | Records |
|---|---|---|
| Providers | host plugin inventory | every transitive `daodan` provider active; otherwise stop with the host's enable or install command |
| Environment | `.venv`, `uv`, `npm`, loop commands | `environment`: interpreter and runners; installation outside the project requires authorization |
| Models | load skill `model-routing:model-routing`, `references/task-routing.md` | `environment.models`: inventory, host support, confirmed per-request assignments |
| Repository and head | `git rev-parse --show-toplevel`, `git rev-parse HEAD` | `base_sha` candidate |
| Working tree | `git status --porcelain=v2 --branch` | staged, unstaged and untracked paths; conflict markers (`u` rows); current branch |
| Interrupted operation | presence of `MERGE_HEAD`, `rebase-merge` or `rebase-apply` under the git directory | blocks the phase |
| Upstream distance | `git fetch --prune`, then `git rev-list --left-right --count HEAD...@{upstream}` | ahead and behind counts; never a blind pull |
| Map context | `codebase-map:map-method`; `references/context-cycle.md` preflight | verify freshness, refresh stale or missing scope, freeze base, packet and I1 before interview |
| Test baseline | the project's declared test command on the scope's tests | `GREEN`; `KNOWN_RED` with the failure fingerprint the user accepted; `UNKNOWN_RED` |
| Migrations | the project's migration status command when one is declared | `ALIGNED`, `PENDING`, `DIVERGED`, `UNKNOWN` or `NOT_APPLICABLE` |

Hash failing tests: unchanged known; changed unknown.

## Model binding persistence

Load `model-routing:model-routing` for per-job bindings; pass confirmed assignments
to Work Controller. Its engine neither calls models nor discovers host identity.
Never hardcode models or host aliases.

Store the confirmed routing artifact in
`environment.models.assignments[request_sha256]` using loaded
`work-controller:work-record`: `run_state.py update --project ROOT --run-id ID
--session ID --expected-revision N --payload PATCH.json`. Preserve interpreter, commands and
existing assignments. Revision conflict: reread and merge. Resume: pass persisted assignments to routing for revalidation.

## Workspace mode

Load `worktree-manager:worktree-method`; follow its creation/reuse and runtime
probe contract. Honor recorded user/project policy; otherwise new Git-bound
tasks use `WORKTREE`. Reuse requires matching repository, branch, task and holder.

| Mode | Use when | Consequence |
|---|---|---|
| `WORKTREE` | default or selected | main checkout's `.daodan/worktrees/`; task-associated naming; parallel waves allowed |
| `BRANCH` | selected | current checkout, project naming; sequential waves |
| `IN_PLACE` | selected | sequential waves; protect preexisting edits from rollback |

Record task ID, branch and path. Prove host read/write/check access before run
initialization: project paths are immutable. Never nest state homes. Resume
failed setup under existing authorization; do not recreate checkouts or install
global hooks.

For test files or services missing from the worktree (env, schema, fixtures),
record `path`, `kind` and `secret`. Reference secrets; never copy their values.

## Special situations

| Situation | Rule |
|---|---|
| Interrupted merge or rebase | Stop; offer to resolve it first. |
| Behind upstream | Offer rebase, fast-forward or a pinned `base_sha` with recorded gap. |
| `UNKNOWN_RED` baseline | No feature starts on a broken base: offer a repair of the failing oracle, a repair wave first, or `KNOWN_RED` with the user's explicit word. |
| `PENDING` or `DIVERGED` migrations | Warn before any test that touches the schema; a worktree gets its own schema binding. |
| Dirty `IN_PLACE` | Protect preexisting paths; intersecting `write_set` stops with `NEEDS_REPLAN`. |
| Stale map on the scope | Run the incremental update now; the interview reads a fresh map or names the stale paths as unknown. |

Write `workspace`, `preflight` and `environment`; state mode, base commit and baseline.
