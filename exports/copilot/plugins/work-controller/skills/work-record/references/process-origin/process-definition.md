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

# Process definition

The runtime accepts one YAML document with schema `process-controller/process/v1` and kind `graph`. The legacy `deadly-brain/process/v1` schema remains accepted for compatibility. Validation is closed: unknown fields, unknown component kinds, missing producers, duplicate artifact producers, cycles and paths outside the workspace are rejected.

```yaml
schema: process-controller/process/v1
kind: graph
id: api-review
objective: Review the public API and record a verified report
jobs:
  - id: analyze
    type: agent
    summary: Inspect the API and write a bounded report
    produces:
      - name: report
        type: markdown
        path: artifacts/report.md
    write_set: [artifacts/report.md]
    max_attempts: 2
    timeout_seconds: 300
  - id: review
    type: agent
    summary: Verify the report against the API contract
    needs: [analyze]
    consumes: [report]
    produces:
      - name: review
        type: markdown
        path: artifacts/review.md
    write_set: [artifacts/review.md]
budget:
  max_attempts: 20
  max_seconds: 3600
```

## Inputs and dependencies

An entry in `consumes` names either a process-level external input or an artifact declared in another job's `produces`. A producer dependency is added automatically; `needs` declares additional ordering without inferring dependencies from source-code call edges.

```yaml
inputs:
  - name: source
    type: markdown
    path: docs/input.md
```

External files are copied into the content-addressed store at run admission. Their later mutation does not change the bytes bound to that run.

## Job kinds

`agent` creates a host packet. The host must start the attempt, perform the work and complete it with a unique event ID. `command` executes an argv array without a shell and requires the run's `shell` grant. Its exit code is the deterministic gate. Both kinds use the same artifact and attempt contracts.

Every produced path must be declared in `write_set`. Artifact admission requires the file to exist and be copied successfully into the immutable store. The engine does not claim that this proves semantic correctness; use downstream verification jobs for independent checks.

`write_set` is a scope contract, not an operating-system sandbox. Command jobs execute trusted argv with the user's permissions, and agent jobs run through the host. Grant execution only to definitions you authorize; an installed-host adapter must prove any stronger confinement it claims.

## Partial commits

A job may declare:

```yaml
commit:
  message: "process-controller: update API review"
```

The run needs the separate `commit` grant and a clean Git baseline. After the job's outputs pass admission preparation, the engine stages only the declared write set, rejects staged paths outside it and records the resulting commit SHA in the attempt. YAML alone never supplies the grant.

## Immutable admission

A run stores both the normalized definition digest and the source YAML digest. It also binds the workspace used for every subsequent handoff and completion. Changing a file after admission does not mutate the active definition. Revision and selective replan are not part of the first slice; start a new run instead.
