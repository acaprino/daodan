<daodan_host_binding host="copilot">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Copilot binding: repository reads use search, writes use edit, shell execution uses
runCommands and network fetch uses fetch in the adapter's tool allowlist. Custom
agent dispatch uses the agent allowlist alias; the current CLI documents a task
dispatch tool. Call the mechanism actually registered in this session, not an
allowlist alias assumed to be a callable tool.
Use each registered tool's input fields; Claude's subagent_type, role and
run_in_background fields are not a portable dispatch schema. Dispatch only the
custom agent named by the generated owner-qualified binding and agents allowlist.
An omitted tools restriction retains host defaults; an explicit list constrains
the worker and does not grant omitted shell, write or MCP tools.
Skills use their exact installed registry identity; workflows are prompt entries.
A dispatched workflow also has its generated <workflow>-coordinator custom agent.
Required foreign providers use Copilot's marketplace/install commands:
copilot plugin marketplace add <source>, then copilot plugin install <provider>@<marketplace>.
Register plugin-declared MCP server commands in this host's MCP configuration as
the generated note directs. Registration and a dependency declaration alone do
not demonstrate that browser/server tools are callable by the selected worker.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Coordinator MCP allowances use <declared-server>/* for only the package's named
servers. This requires actual server registration and tool discovery; it grants
no undeclared server and does not prove MCP is callable in an installed run.
Schema reference: https://docs.github.com/en/copilot/reference/custom-agents-configuration

The executing agent and its coordinator own continuation, recovery, verification
and delivery. Skills supply knowledge and method instructions; they are not
executors or a runtime persistence mechanism.

Resolve each component by kind and exact installed identity. A role is dispatched
as a worker, a skill loads instructions, and a workflow starts its declared method.
Kernel owner-qualified skill references are logical provider identities: resolve
them to the actual host registry name and verified installed provider path. Do not
invent a registry string by adding an owner's prefix when the host does not use it.
Do not load an agent identity as a skill or execute a workflow name as a shell
command. Declared required foreign providers remain mandatory. If a required
provider or capability (including required MCP access or isolation) is unavailable,
stop its dependent phase and report the missing capability. Optional external
providers follow the method's declared selection and absence behavior; their
absence alone does not block the base workflow. Report any explicitly requested
but unavailable provider contribution as unfulfilled and continue independent
work. Do not install a different host's plugin or
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

Probe; record `workspace` and `preflight`. No product edits.

## Probes

| Probe | Command | Records |
|---|---|---|
| Providers | host plugin inventory | every transitive `daodan` provider active; otherwise stop with host-specific enable/install command |
| Environment | `.venv`, `uv`, `npm`, loop commands | `environment`: interpreter/runners; installation outside the project requires authorization |
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

Store confirmed routing in `environment.models.assignments[request_sha256]`
through `work-controller:work-record`: `run_state.py update --project ROOT --run-id ID
--session ID --expected-revision N --payload PATCH.json`. Preserve interpreter/commands/assignments.
Revision conflicts require reread/merge; resume revalidates persisted assignments through routing.

## Workspace mode

Load `worktree-manager:worktree-method`; follow its creation/reuse and runtime
probe contract. Honor recorded user/project policy; otherwise new Git-bound
tasks use `WORKTREE`. Reuse requires matching repository, branch, task and holder.

| Mode | Use when | Consequence |
|---|---|---|
| `WORKTREE` | default or selected | main checkout's `.daodan/worktrees/`; task-associated naming; parallel waves allowed |
| `BRANCH` | selected | current checkout, project naming; sequential waves |
| `IN_PLACE` | selected | sequential waves; protect preexisting edits from rollback |

Record task ID/branch/path. Prove host read/write/check access before run
initialization: project paths are immutable. Never nest state homes. Resume
failed setup under existing authorization; do not recreate checkouts or install
global hooks.

For an approved specification, preserve its exact bound project-relative path
and SHA-256 in the selected checkout; never overwrite foreign work. Verify bytes
and approval through `references/specification.md` before planning.

For missing worktree test files/services (env, schema, fixtures), record
`path`/`kind`/`secret`. Reference secrets; never copy values.

## Special situations

| Situation | Rule |
|---|---|
| Interrupted merge or rebase | Stop; offer to resolve it first. |
| Behind upstream | Offer rebase, fast-forward or a pinned `base_sha` with recorded gap. |
| `UNKNOWN_RED` baseline | No feature starts on a broken base: offer oracle repair, a repair wave first, or `KNOWN_RED` with explicit user acceptance. |
| `PENDING` or `DIVERGED` migrations | Warn before schema-touching tests; bind the worktree's own schema. |
| Dirty `IN_PLACE` | Protect preexisting paths; intersecting `write_set` stops with `NEEDS_REPLAN`. |
| Stale map on the scope | Update incrementally now; interview reads a fresh map or names stale paths unknown. |

Write `workspace`, `preflight` and `environment`; state mode, base commit and baseline.
