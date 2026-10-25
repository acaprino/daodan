# Phase 1: preflight and workspace

Probe first; record `workspace` and `preflight`. Do not edit project files.

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

Hash sorted failing test identifiers: unchanged means known; changed means unknown.

## Model binding persistence

Store the confirmed routing artifact in
`environment.models.assignments[request_sha256]` using loaded
`work-controller:work-record`: `run_state.py update --project ROOT --run-id ID
--session ID --expected-revision N --payload PATCH.json`. Preserve interpreter, commands and
existing assignments. Revision conflict: reread and merge. Resume: pass persisted
assignments to routing for request, confirmation, inventory and capability checks.

## Workspace mode

Present probes; ask once with a recommended default:

| Mode | Recommend when | Consequence |
|---|---|---|
| `WORKTREE` | more than one wave, parallel tasks, or a dirty working tree | a worktree under the project's declared worktree root on branch `task/<run>-<slug>`; parallel waves allowed; removed at integration |
| `BRANCH` | a clean tree and a task the user wants on its own branch | branch `task/<run>-<slug>` in the checkout; waves run sequentially |
| `IN_PLACE` | a small task on the current branch | waves run sequentially; every preexisting modified file is recorded as protected and never restored by a rollback |

For test files or services missing from the worktree (env, schema, fixtures),
record `path`, `kind` and `secret`. Reference secrets; never copy their values.

## Special situations

| Situation | Rule |
|---|---|
| Interrupted merge or rebase | Stop; offer to resolve it first. |
| Behind upstream | Offer rebase or fast-forward, or pin `base_sha` to the current head with the gap recorded. |
| `UNKNOWN_RED` baseline | No feature starts on a broken base: offer a repair of the failing oracle, a repair wave first, or `KNOWN_RED` with the user's explicit word. |
| `PENDING` or `DIVERGED` migrations | Warn before any test that touches the schema; a worktree gets its own schema binding. |
| Dirty tree and `IN_PLACE` | Record protected paths; a task whose `write_set` intersects them stops with `NEEDS_REPLAN`. |
| Stale map on the scope | Run the incremental update now; the interview reads a fresh map or names the stale paths as unknown. |

Write `workspace`, `preflight` and `environment`; state mode, base commit and baseline.
