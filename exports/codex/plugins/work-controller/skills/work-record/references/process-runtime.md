> `<plugin-root>` names the directory that holds this plugin's `.codex-plugin/plugin.json`. Resolve it once from where this file was loaded, then substitute it into every path below that starts with it.

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

# Work Controller process runtime

The canonical implementation, console assets, CLI and read-only MCP server ship
inside `work-controller@daodan`. Work Controller has no dependency on a consumer
plugin. Consumers keep their domain rules, archetypes, model bindings and review
methods. Read the work-record skill's working discipline before execution.

## Launcher and state

Use this command prefix, substituting the installed plugin root:

```text
uv run --no-config --no-project --script "<plugin-root>/skills/work-record/scripts/controller.py"
```

The launcher requires Python 3.11 or newer and the narrowly scoped PyYAML runtime
dependency declared in its script metadata. The compiler remains stdlib-only.
Arguments `--workspace ROOT` and `--home PATH` precede the subcommand. By default,
the process store is `.daodan/processes` in the main checkout resolved by the
existing run-record helper; worktree records and process state share that home.
The engine uses SQLite metadata and a content-addressed artifact store.

Validation creates no runtime state. A state-changing command creates a dedicated
record home and its sentinel when needed. Existing `.process-controller` or
`.deadly-brain` stores require explicit `--home` selection; never silently choose,
merge or relocate stores. An explicit old home retains its `process.db` or
`brain.db` database. Do not rewrite stored YAML, normalized schema values,
definition digests or old records when changing names.

Console and MCP startup may initialize an empty dedicated store so a newly
installed interface can start before the first process. Their read tools never
admit work, change runs or grant execution. Existing non-dedicated record homes
are still rejected.

New definitions use `work-controller/process/v1`. Both previous schema identifiers
remain accepted, retaining their supplied values and hashes. Default composed
output is `work-controller.yaml`. The retained `analysis` and `change` archetypes
are compatibility conveniences; domain workflows supply their exact approved
graph rather than treating those examples as mandatory universal software rules.

## Execution

1. Compose a definition with `compose --objective TEXT --output FILE`, or author
   the approved YAML directly. `interview --id ID` resumes a persisted interview.
   Run `validate FILE` for integrity-only admission checks without execution.
2. Admit with `start FILE --run-id PROCESS`. Command jobs need the explicit
   `--grant shell`. Optional generic Git jobs need a separate `--grant commit`
   and a clean Git work-tree root. These grants never authorize push or deletion.
3. `drive PROCESS --holder SESSION` executes argv command jobs and returns a
   bounded packet at an agent job. The coordinator dispatches the actual allowed
   host worker and records its handle; a packet creates no registered role,
   supported model or confinement mechanism.
4. Use `start-attempt ATTEMPT --holder SESSION` before work. After the declared
   output exists, `complete ATTEMPT --holder SESSION --event-id EVENT --verdict pass`
   admits its artifacts. Use `--verdict fail --error TEXT` for failure. Drive again
   until the graph is complete. A file or stopped worker alone is no delivery.
5. Use bounded `status`, `frontier`, `packet` and paginated `events` to inspect it.
   `resume PROCESS` revokes reserved work and marks running work unknown; never
   duplicate dispatch blindly. `retry-attempt ATTEMPT --confirm-stopped` follows
   evidence that its worker stopped. An uncertain Git outcome needs a verified
   `--commit-sha SHA` or explicit `--discard-commit-outcome` after reconciliation.

Jobs use argv without a shell. Their write sets are declared boundaries, not an
operating-system confinement guarantee. Keep budgets, unsafe YAML rejection,
artifact-path protections, idempotency and conservative resume intact. The
`supervise ATTEMPT` recommendation cannot admit results or change graph authority.
Decision maps (`map-open`, `ticket-add`, `map-next`, `ticket-claim`, `ticket-close`,
`map-status`, `map-events`) retain their distinct ticket frontier and evidence rules.

## Bind a process to a work record

New process-backed work sets `process_required: true` at init. Prepare the graph
from the approved task and declare its expected worker deliveries in the work
record before dispatch. Review deliveries kept outside the graph still use the
existing work-record ledger. Every graph agent job must map to a native report;
different independent deliveries require different process artifacts.

After graph admission, write this payload with the returned definition digest:

```json
{
  "schema": "daodan/process-binding/v1",
  "run_id": "analysis-process",
  "definition_digest": "<admitted 64-character SHA256>",
  "deliveries": {
    "analysis-worker": {"job": "analyze", "artifact": "report"},
    "analysis-reviewer": {"job": "review", "artifact": "review"}
  }
}
```

Call `run_state.py bind-process --project ROOT --run-id WORK --session SESSION
--expected-revision N --payload BINDING.json`. It verifies the process in the
canonical store, its workspace, immutable digest, job/output declarations and
work delivery identities. Binding grants nothing and cannot be replaced; a
different graph requires a new work record. Bind before starting a required
wave task. Legacy unbound JSON runs continue through their recorded method.

For a process-backed delivery, admit the engine artifact first, retain identical
bytes as the run-owned native report, then mark its work delivery delivered.
This also works for linked worktrees, whose native reports live in the main
checkout's record home. Validation opens the existing store read-only and checks
the successful producer, admitted artifact, content-addressed bytes and report
digest. Do not fabricate receipts from engine events. Result envelopes include
the same `process` object as their work record.

Process success is necessary for a bound work record's completion. All existing
questions, deliveries, candidate snapshots, reviews, gates and authorizations
remain necessary too. Domain commits stay in the existing reviewed wave method;
bound graphs must omit engine commit jobs/grants. Generic explicit CLI Git support
remains available for separately authorized processes outside this domain binding.

## Interfaces and compatibility

`console --port PORT` binds to loopback and prints a temporary tokenized URL. Keep
it in a supported background process, retain its handle and stop it explicitly
when the user finishes. The console shares bounded read models with `mcp`, which
reserves stdout for JSON-RPC and exposes read tools only. Keep `process_*` tool
names and existing token headers/storage keys for client compatibility. The
plugin's generated registration note supplies the exact command on each host;
registration is not evidence of installed-host execution.

The imported engine implements sequential graph execution, deterministic
composition, durable attempts, artifacts, decision tickets, supervision advice
and local read interfaces. Real host dispatch adapters, observed model identity,
parallel execution, dynamic loops, selective replan and semantic memory remain
separate unimplemented capabilities. A source transfer does not prove them.
Historical source documents under `process-origin/` are provenance records, not
current launcher or execution instructions.
