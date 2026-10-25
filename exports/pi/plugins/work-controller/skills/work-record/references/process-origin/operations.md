<daodan_host_binding host="pi">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
Core Pi supplies neither subagent nor MCP. Isolated workers require pi-subagents:
pi install npm:pi-subagents. Use that extension's registered subagent schema and
pass the full rendered role body inline. Role skills named <plugin>-<role> are
body resources with automatic invocation disabled, not a built-in named agent.
Workflow prompt entries use /<plugin>-<workflow>; ordinary skills use their exact
registered names. If isolation is mandatory and unavailable, stop the phase.
MCP requires pi-mcp-adapter: pi install npm:pi-mcp-adapter, then register the
generated server command in its supported MCP configuration.
Keep the selected package's full local dependency closure. Provision qualified
foreign providers as skills/resources this runtime can load; Pi does not install
another host's marketplace plugin from a Claude install command.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Kernel <owner>:<skill> references identify the logical provider. Ordinary Pi
skills retain their source frontmatter name, so resolve the actual registered name
and provider path from the active inventory; do not invent a prefixed native ID.

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

# Operations

## State ownership

SQLite stores current state and append-only events in the same immediate transaction. A claim creates the attempt before dispatch. A completion stores artifact metadata, delivery and job transition atomically. Artifact bytes are immutable in the content-addressed store.

The initial executor is sequential. A second local process cannot claim a job while another attempt is reserved or running. Parallel and distributed execution require a separate verified adapter.

The default runtime home is `.process-controller`. If only the legacy `.deadly-brain` home is present, it is used as a compatibility fallback.

## Attempt lifecycle

```text
pending → reserved → running → completing → delivered
                    │             ├────────→ failed → new attempt, if budget remains
                    │             └────────→ running after an ordinary aborted completion
reserved → revoked → pending
running/completing → unknown → blocked run → explicit failed reconciliation
```

Completion is admitted before artifact ingestion or Git effects. The admission records holder, event and request. Concurrent duplicates cannot repeat those effects. An ordinary failure appends `delivery.aborted` and permits a bounded retry; a crash leaves the attempt uncertain. Internal event IDs use a reserved namespace, so a client delivery cannot block run completion.

`resume` does not infer a result. Reserved work is revoked; running work becomes unknown and stops new admissions. `retry-attempt --confirm-stopped` records the user's reconciliation before another attempt can start.

## Completion

A run finishes only when every declared job is succeeded. Attempt exhaustion, deadline exhaustion, unknown worker state and unfinished obligations prevent completion. A supervisor's `FINISH` recommendation does not close the run; `finish` performs its own check.

A run is bound to the workspace recorded at admission. Packets, command execution, completion, resume and finish reject a different workspace instead of silently importing artifacts or running work from another directory.

## Logs and bounded output

Command stdout and stderr go to per-attempt log files, not into the journal or CLI result. Status, frontier, packets and event pages return bounded views. Artifact bodies are read through their content path only by consumers that need them.

## Git safety

Commit support requires a clean work-tree at run admission and the workspace must be the work-tree root, so scoped paths and staged paths use the same coordinates. The runtime home must be ignored by that work-tree or live outside it, otherwise the home itself makes the baseline dirty. A created SHA is recorded before final delivery, allowing an ordinary database retry to avoid a duplicate commit.

If Git succeeds but `rev-parse` or SHA persistence fails, the attempt becomes `unknown` and the run blocks instead of retrying blindly. Reconcile with `--commit-sha` after inspecting HEAD, or use `--discard-commit-outcome` only after verifying that no commit exists. The first path resumes the same completion without another commit; the second opens a new attempt. Tests use fake Git runners and do not mutate a real repository. Live Git verification, behavior with preexisting staged changes and host-specific work-tree handling remain separate operational checks. The engine never runs push, reset, rebase or clean.
