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

# Phases 4 and 5: plan and execution

## Compile the plan

Translate the record into micro-tasks and group them into waves. Every task
carries `id`, `write_set`, `oracle` (command and the failure it must produce
before the change), `verification` command, and when relevant
`resource_locks`, `produces`, `consumes`, the `EX-*` it makes pass and the
`INV-*` it enforces. Order callees before callers along the map's resolved
edges. The first wave builds missing fixtures or harnesses when the oracles
need them.

Run the protocol helper's `plan-check` on the draft. It refuses more than
four files in a `write_set` without a reasoned exception, two tasks of one
wave that share a file, a lock or a produced-consumed contract, a parallel
wave outside a `WORKTREE` workspace, and a missing oracle. Correct the plan
until it passes, then write it into the run's `waves` section.

## Review of the plan (stage B)

Run `senior-review:review-method` with shape `light`, kind `plan` and stage
`plan`: `plan-check` has settled the structure, and the premise auditor checks
every cited path, symbol and caller and that each oracle can fail for its
stated reason. Three planner-and-review rounds at most, then the user. Present the
approved plan with its expected cost and stop for approval, unless the
authorization already covers execution.

## Execute a wave

For each task, in the order the wave fixes (parallel only in a `WORKTREE`):

1. Record `pre_phase_sha` and the pre-step bytes of every `write_set` file
   through the protocol helper.
2. Dispatch the writer with the brief of `references/worker-brief.md`:
   for Python dispatch `python-development:python-engineer`,
   for TypeScript and JavaScript dispatch `typescript-development:typescript-engineer`,
   for tests only dispatch `testing:test-writer`, for any
   other stack the isolated worker, with the knowledge selected when you
   load the `skill-catalog:skill-catalog` skill. The writer runs the oracle first and stops with
   `ORACLE_INVALID` when it passes or fails for another reason; writes only
   inside `write_set` and stops with `NEEDS_REPLAN` when another file must
   change; runs the verification; records a ruling for any local decision the
   record did not make; returns `OK` with the changed paths.
3. On `OK`, confirm that the changed paths are a subset of `write_set`, run
   the verification again in this context, and commit atomically when
   authorized (otherwise record the candidate snapshot). The message is
   `<type>(<area>): <task title>` with the trailer
   `Daodan-Task: <run id> wave <n>/<m>`, so `git log` shows progress. On any other code,
   restore the task's `write_set` from the pre-step bytes, remove files the
   task created, touch nothing else, and record the attempt.
   `NEEDS_REPLAN` returns to the plan with the missing file; `ORACLE_INVALID`
   returns to the record or the test.

## Review of the wave (stage C)

With every task committed or its candidate recorded, run
`senior-review:review-method` with shape `light` and stage `wave-<n>` on the
wave's diff: the project's tools, then the generalist, with the record's
`EX-*` and `INV-*` and the wave's rulings as its intent. A `BLOCK` reopens the task; the
wave is `sealed` only with every task committed and the review delivered.
Then the next wave.

`clean-code:readability-method` may run once per wave, after the review
with the oracles green, when the user asked.
