<daodan_host_binding host="claude">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Claude binding: repository tools are Read/Glob/Grep and Write/Edit; shell execution
uses Bash and network fetch uses WebFetch. Pass the executable string in Bash's
command field, and use its registered timeout/background schema. Worker dispatch
uses the available native Agent mechanism and its registered agent-selection and
prompt fields. Do not turn a prose role label into an invented role argument.
Inherit the session model unless the declared workflow and active schema permit an
override. Load installed skills by qualified ID; named roles use their owning
plugin's agent identity, while workflow entries use /<plugin>:<workflow>.
Required foreign providers use Claude's marketplace/install commands:
claude plugin marketplace add <source>, then claude plugin install <provider>@<marketplace>.
A declared package MCP server is configured through the generated MCP manifest;
still check its tools are actually available in the active session.

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

Run `senior-review:review-method` with `target-kind=plan` and budget `delta`
on the plan. The preparation selects the premise lens (every cited path,
symbol and caller exists in the current tree), the test lens (every oracle
fails for the right reason and cannot pass trivially), the initialization
lens (ordering, hidden shared files, migrations), the abstraction lens (no
second owner for an existing concept) and the stack lenses of the named
files. Up to three planner-and-lenses rounds, then the user. Present the
approved plan with its expected cost and stop for approval, unless the
authorization already covers execution.

## Execute a wave

For each task, in the order the wave fixes (parallel only in a `WORKTREE`):

1. Record `pre_phase_sha` and the pre-step bytes of every `write_set` file
   through the protocol helper.
2. Dispatch the writer with the brief of `references/worker-brief.md`:
   `python-development:python-engineer` for Python,
   `typescript-development:typescript-engineer` for TypeScript and
   JavaScript, `testing:test-writer` for a task that writes tests only, the
   isolated worker with the knowledge `skill-catalog:skill-catalog` selected
   for any other stack. The writer runs the oracle first and stops with
   `ORACLE_INVALID` when it passes or fails for another reason; writes only
   inside `write_set` and stops with `NEEDS_REPLAN` when another file must
   change; runs the verification; records a ruling for any local decision the
   record did not make; returns `OK` with the changed paths.
3. On `OK`, confirm that the changed paths are a subset of `write_set`, run
   the verification again in this context, and commit atomically when
   authorized (otherwise record the candidate snapshot). On any other code,
   restore the task's `write_set` from the pre-step bytes, remove files the
   task created, leave everything else untouched, and record the attempt.
   `NEEDS_REPLAN` returns to the plan with the missing file; `ORACLE_INVALID`
   returns to the record or the test.

## Review of the wave (stage C)

When every task of the wave is committed or its candidate is recorded, run
`senior-review:review-method` with budget `delta` on the wave's diff. The
preparation selects the logic lens for conformance to `EX-*` and `INV-*`, the
test lens for the new oracles, the premise lens on every new ruling, and the
stack lenses the diff activates. A blocking finding reopens the task; the
wave is `sealed` only with every task committed and the review delivered.
Then the next wave.

`clean-code:readability-method` may run once per wave on the wave's files,
after the review and with the oracles green, when the user asked for it.
