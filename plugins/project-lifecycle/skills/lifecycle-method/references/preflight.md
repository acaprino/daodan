# Phase 1: preflight and workspace

Probe before asking. Every fact below is recorded in the run's `workspace`
and `preflight` sections through the protocol helper; nothing here edits
project files.

## Probes

| Probe | Command | Records |
|---|---|---|
| Providers | the host's plugin inventory | every required provider active; a missing one stops here with the host's enable or install command |
| Environment | `.venv`, `uv`, `npm`, the loop block's commands | `environment`: the interpreter and runners every command uses; installing outside the project needs explicit authorization |
| Repository and head | `git rev-parse --show-toplevel`, `git rev-parse HEAD` | `base_sha` candidate |
| Working tree | `git status --porcelain=v2 --branch` | staged, unstaged and untracked paths; conflict markers (`u` rows); current branch |
| Interrupted operation | presence of `MERGE_HEAD`, `rebase-merge` or `rebase-apply` under the git directory | blocks the phase |
| Upstream distance | `git fetch --prune`, then `git rev-list --left-right --count HEAD...@{upstream}` | ahead and behind counts; never a blind pull |
| Map freshness | `codebase-map:map-method`: `snapshot.py diff --verify` on the scope against the current tree | stale paths; triggers an incremental update before the interview |
| Test baseline | the project's declared test command on the scope's tests | `GREEN`; `KNOWN_RED` with the failure fingerprint the user accepted; `UNKNOWN_RED` |
| Migrations | the project's migration status command when one is declared | `ALIGNED`, `PENDING`, `DIVERGED`, `UNKNOWN` or `NOT_APPLICABLE` |

Baseline fingerprint: the sorted failing test identifiers, hashed; the same
fingerprint later is the same known failure, a different one is unknown.

## Workspace mode

Present the probes in one screen and ask the user once, with a recommended
default:

| Mode | Recommend when | Consequence |
|---|---|---|
| `WORKTREE` | more than one wave, parallel tasks, or a dirty working tree | a worktree under the project's declared worktree root on branch `task/<run>-<slug>`; parallel waves allowed; removed at integration |
| `BRANCH` | a clean tree and a task the user wants on its own branch | branch `task/<run>-<slug>` in the checkout; waves run sequentially |
| `IN_PLACE` | a small task on the current branch | waves run sequentially; every preexisting modified file is recorded as protected and never restored by a rollback |

A worktree needs environment bindings: for each file or service the tests
need and the worktree lacks (an env file, a schema, a fixture directory),
record `path`, `kind` and `secret`. A secret binding is a reference, never a
copied value.

## Special situations

| Situation | Rule |
|---|---|
| Interrupted merge or rebase | Stop; offer to resolve it first. |
| Behind upstream | Offer rebase or fast-forward, or pin `base_sha` to the current head with the gap recorded. |
| `UNKNOWN_RED` baseline | No feature starts on a broken base: offer a repair of the failing oracle, a repair wave first, or `KNOWN_RED` with the user's explicit word. |
| `PENDING` or `DIVERGED` migrations | Warn before any test that touches the schema; a worktree gets its own schema binding. |
| Dirty tree and `IN_PLACE` | Record protected paths; a task whose `write_set` intersects them stops with `NEEDS_REPLAN`. |
| Stale map on the scope | Run the incremental update now; the interview reads a fresh map or names the stale paths as unknown. |

Close by writing `workspace`, `preflight` and `environment` to the run and
restating mode, base commit and baseline in one line.
