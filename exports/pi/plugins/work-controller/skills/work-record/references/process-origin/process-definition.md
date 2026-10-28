<daodan_host_binding host="pi">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Bodies name operations, never tools: repository read, file discovery, content
search, repository write, repository edit, shell execution, network fetch, network
search, user question and worker dispatch. The host binding below maps each one to
a registered tool. An operation it leaves unbound, or whose tool is absent from
this session, is unavailable: report it as missing, never search for a tool named
after the operation.

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
Core Pi has no network tool: network fetch and network search run as shell
commands, and a user question is asked in the reply while the run waits for the
answer.
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
