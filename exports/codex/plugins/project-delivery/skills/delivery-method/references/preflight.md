<daodan_host_binding host="codex">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Codex binding: the adapter binds repository read to read_file, writes to
apply_patch and shell execution to shell; use the equivalent registered tools of
the active Codex runtime and their actual fields. In particular, a shell example's
command, timeout and background fields are not automatically another runtime's
cmd, yield_time_ms or session controls.
Start the runtime's available isolated subagent mechanism with the complete
rendered role body in its task prompt. Role Markdown and generated dispatch bodies
are resources, not registered skills or a native role/subagent_type parameter.
Use only declared role bindings and report an unavailable isolation mechanism.
Load installed skills by their advertised exact IDs; workflow skills carry the
<workflow>-workflow suffix. Named-agent examples do not override inline delivery.
Required foreign providers use Codex's marketplace/install commands:
codex plugin marketplace add <source>, then codex plugin add <provider>@<marketplace>.
Register plugin-declared MCP servers through the active host's MCP configuration
using the generated server command. Do not assume registration makes every tool
available to a restricted worker.
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
