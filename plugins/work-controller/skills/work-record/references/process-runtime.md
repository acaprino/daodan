# Work Controller process runtime

The canonical implementation, console assets, CLI and read-only MCP server ship
inside `work-controller@daodan`. Work Controller has no dependency on a consumer
plugin. Consumers keep their domain rules, archetypes, model bindings and review
methods. Read the work-record skill's working discipline before execution.

## Launcher and state

Use this command prefix, substituting the installed plugin root:

```text
uv run --no-config --no-project --script "${CLAUDE_PLUGIN_ROOT}/skills/work-record/scripts/controller.py"
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
