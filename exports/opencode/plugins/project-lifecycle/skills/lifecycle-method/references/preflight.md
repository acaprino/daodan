<daodan_host_binding host="opencode">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

OpenCode V2 binding: repository reads use read/glob/grep, writes use write/edit/patch,
shell execution uses shell, network tools are webfetch/websearch, and clarification
uses the registered question tool. shell takes command, optional workdir, timeout
in milliseconds and background. It does not provide interactive stdin. Persistent
capture uses background: true and an explicit noninteractive stop signal.
Load skills with skill using id: "<plugin>:<skill>". Dispatch registered roles with
subagent using agent: "<owner>:<role>", description and prompt; optional sessionID
continues that child, and background: true requests asynchronous completion.
Use only roles allowed by the current harness and permissions. A child cannot
dispatch nested workers when its permissions or the configured depth deny it.
Workflow entries are /<plugin>:<workflow>, registered by the package loader.
Inherit the session model; an override requires its authorized, actually available
provider/model identity, not another host's short model alias.
The loader includes required local providers and registers plugin-declared MCP
servers. Qualified foreign providers need a compatible V2 plugin/skill provisioned
through this host, never a Claude marketplace command. Check the active registry:
registration metadata alone does not prove a connected server or usable tool.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.

The executing agent and its coordinator own continuation, recovery, verification
and delivery. Skills supply knowledge and method instructions; they are not
executors or a runtime persistence mechanism.

Resolve each component by kind and exact installed identity. A role is dispatched
as a worker, a skill loads instructions, and a workflow starts its declared method.
Kernel owner-qualified skill references are logical provider identities: resolve
them to the actual host registry name and verified installed provider path. Do not
invent a registry string by adding an owner's prefix when the host does not use it.
Do not load an agent identity as a skill or execute a workflow name as a shell
command. Named foreign providers remain mandatory. If an installed provider, MCP
server or required isolation mechanism is unavailable, stop its dependent phase
and report the missing capability. Do not install a different host's plugin or
substitute unrelated skills to claim coverage.

Shell execution alone does not establish interactive stdin. Before a capture or
checkpoint, use an available session-control mechanism. When stdin is unavailable,
keep user-driven capture in a supported background process with bounded output and
an explicit stop signal controlled by the coordinator after the user's completion
message. Close owned browser/process resources on completion or cancellation.

Continue working within the current authorization while the requested result is
achievable. After a tool error, inspect its cause, correct the relevant input or
implementation, retry when justified and verify the outcome; never repeat a
failing action blindly. Do not close the turn with a promise or a partial result
when an authorized next step can still produce or verify the requested result.
Stop only for a documented real impediment, a missing required capability, an
unresolved human decision or the caller's stop request. At that boundary, report
completed results, remaining work and the concrete prerequisite for continuation;
continue any independent work that the blocker does not prevent.

A tool's successful exit, a worker stop or an idle session is not the deliverable.
Return final text naming observed findings, artifact paths, executed checks and
blockers. An empty worker result is missing delivery: inspect or resume that worker
when permitted, or record failure. Verify required artifacts and candidate gates
before marking the requested outcome complete.

This is an execution binding, not a rewrite of source examples. Preserve programming
language fences, domain code and host APIs that are the subject of marketplace-ops
or agent-sdk-builder. A host-as-subject API is not a tool provided to this session.
Compiled binding and static checks do not prove an installed host executed a run.
</daodan_host_binding>

# Phase 1: preflight and workspace

Probe before asking. Every fact below is recorded in the run's `workspace`
and `preflight` sections; nothing here edits project files.

## Probes

| Probe | Command | Records |
|---|---|---|
| Providers | the host's plugin inventory | every plugin the `daodan` entry requires, transitively, active; a missing one stops here with the host's enable or install command |
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
