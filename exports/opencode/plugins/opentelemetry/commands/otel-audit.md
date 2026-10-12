---
description: 'Report on an existing Python deployment: what is broken, where, and the fix. TRIGGER WHEN: the user asks to review, audit, or validate OTel instrumentation: span hygiene, context propagation, exporter config, sampling, async handling, attribute budgets, or AWS X-Ray / ADOT setup. DO NOT TRIGGER WHEN: building new instrumentation from scratch (use the otel-architect agent), or non-OTel observability (Datadog APM, Sentry).'
---

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

# otel-audit

<!-- Generated by the Daodan compiler for opencode. Edit the kernel, never this file. -->

## Execution harness

Selected topology: **parallel-subagents**, with role delivery by **named-agent**, and declared
isolation **required**.

Dispatch one worker per entry in the plan below with the `subagent` tool. Name the role as the
agent, using the qualified identity in the bindings below, and give it a short `description` and the full
task as `prompt`. Each agent runs in a fresh child session, so isolation is native here.
For a local role the qualified form is `agent: "opentelemetry:<role>"`; external roles
use their owner's prefix from the bindings, never the coordinator's prefix.

Under `parallel-subagents`, dispatch every worker of one phase with `background: true`, then wait
for every completion notice before the phase closes; do not poll. Under `serial-isolated`, dispatch
them one at a time in the foreground.

Every role below is registered as an agent by this package. A `subagent` call that answers with an
unknown agent means the install is broken: stop and report it, never continue with a shorter
report.

Coordinator completion ownership: keep the method's owned run and delivery ledger,
including each expected worker, attempt, report path and required check evidence.
Validate report artifacts before recording delivered. An empty final message or
worker stop remains missing delivery: inspect or resume when permitted, otherwise
record failed with the uncovered scope. Follow the declared join and phase gates;
a recorded failure is accounted for, never converted into a successful delivery.
Continue authorized work and recovery until the requested result and its checks
exist or a concrete blocker is recorded. Preserve the exclusive final report owner
and the ledger schema; a tool exit or a promise cannot satisfy completion.

Harness obligations, none of them optional:

- Every dispatched worker runs in its own context and reads only coordinator-declared inputs.
  Independent reviewers never read peer results before their own delivery.
- Follow the dispatch plan below in phase order. A phase starts only after every phase it needs has
  closed, and a phase closes only when every worker it dispatched is recorded `delivered` or
  `failed`. A worker reports delivered or failed in its final message; there is no shared task
  list, so the coordinator keeps that record itself.
- Dispatch only roles from this set, as the phase graph or loaded method requires: `otel-architect`
- A worker writes only what the coordinator assigned to it: its intermediate report and, when its
  task authorizes edits, its assigned files. It never reverts preexisting or foreign changes.
  The final report artifact has one exclusive owner in its declaring phase.

Dispatch plan:

1. `scope`: runs in the orchestrating context; produces `artifact:scope`.
2. `review`: one `otel-architect` in an isolated context; needs `scope`; consumes `artifact:scope`; produces `artifact:otel-audit-report`.

Role bindings:

- `otel-architect`: dispatch the installed `opentelemetry:otel-architect` agent by its qualified identity.

The phase graph and the record schemas are in `contracts/otel-audit.workflow.toml`.

## Method

# OpenTelemetry Audit

Analyze an existing OpenTelemetry Python instrumentation and produce an actionable audit report.

## Instructions

1. **Identify OTel components** in the codebase:
   - SDK setup (`TracerProvider`, `MeterProvider`, `LoggerProvider`)
   - Exporters (OTLP gRPC/HTTP, X-Ray, console)
   - Propagators (W3C TraceContext, B3, X-Amzn-Trace-Id, custom)
   - Instrumentations (auto-instrumentations, manual spans)
   - Samplers (parent-based, trace-id-ratio, always-on)
   - Resource detectors (service.name, service.version, aws.ec2, k8s.pod)
   - Collector / ADOT config (if present)

2. **Audit each dimension** against best practices:

### SDK Setup
- [ ] `TracerProvider` created once at process start, not per request
- [ ] `service.name` and `service.version` resources set (required for most backends)
- [ ] Resource detectors attached (aws-ec2 / k8s / ecs / container detectors for cloud)
- [ ] Shutdown registered (`atexit` or signal handler) to flush spans on exit

### Span Hygiene
- [ ] Spans use `start_as_current_span` (context manager) not raw `start_span` where possible
- [ ] Status set to ERROR only for infrastructure errors; business-logic rejections leave status UNSET
- [ ] `record_exception` used for infrastructure errors, NOT for expected business errors
- [ ] `add_event` used for business-logic events instead of new spans
- [ ] Status is never explicitly set to OK on inner spans (leave UNSET; only the outer request handler may set OK)
- [ ] Span names are low-cardinality (no IDs or user data in the name)
- [ ] Attributes use semantic conventions (`http.request.method`, not `httpMethod`)

### Attribute Budgets
- [ ] No PII in span attributes or baggage (baggage propagates to ALL downstream services)
- [ ] No `None` values in attributes
- [ ] String attributes truncated if potentially long (> 1KB)
- [ ] Span attribute count under the per-span limit (default 128)

### Context Propagation
- [ ] Single `Propagator` chosen intentionally (W3C default, or CompositePropagator for multi-format)
- [ ] Custom transports (AMQP, ZMQ, Kafka, gRPC without auto-instrumentation) inject/extract correctly
- [ ] Propagator instances are module-level or cached (not allocated per call)
- [ ] Async context propagation tested (asyncio, Celery, threading boundaries)

### Async / Threading
- [ ] asyncio: context naturally propagates; verify tasks spawned with `create_task` carry span context
- [ ] Threading: context attached on worker thread entry via `context.attach(ctx)` + `detach(token)` in `finally`
- [ ] Celery: `opentelemetry-instrumentation-celery` installed and configured
- [ ] Batch processors flush on shutdown (not just at the batch interval)

### Exporters
- [ ] OTLP endpoint uses protocol-appropriate port (gRPC 4317 or HTTP 4318)
- [ ] `BatchSpanProcessor` used in production (not `SimpleSpanProcessor`)
- [ ] `max_queue_size` and `schedule_delay_millis` tuned for workload (default 2048 / 5000)
- [ ] TLS configured for OTLP over public networks
- [ ] Compression enabled (`gzip`) for OTLP over HTTP

### Sampling
- [ ] Sampler chosen intentionally (`ParentBasedTraceIdRatio` common default)
- [ ] Ratio appropriate for cost (1.0 in dev, 0.01-0.1 in prod typical)
- [ ] Tail sampling considered if Collector is in the path
- [ ] Error sampling carve-out (always sample error spans) via span processor or Collector

### Logs and Metrics
- [ ] Log correlation goes through the `LoggingInstrumentor` bridge into the existing log pipeline; the Logs SDK (`opentelemetry._logs`) is still experimental, and the leading underscore is intentional
- [ ] Where the Logs SDK is used anyway, `LoggerProvider` set up alongside `TracerProvider` and its experimental status acknowledged
- [ ] Metrics use correct instruments (Counter for monotonic, UpDownCounter for gauges, Histogram for latencies)
- [ ] View / aggregation configured for high-cardinality metrics

### AWS / ADOT (if applicable)
- [ ] `AwsXRayIdGenerator` used for X-Ray compatibility
- [ ] `AwsXRayPropagator` attached (single or composite with W3C)
- [ ] `aws-ec2` / `aws-ecs` / `aws-lambda` resource detectors enabled
- [ ] ADOT sidecar or Lambda layer configured; Collector pipeline `memory_limiter -> batch -> exporters`

### Anti-Patterns to Flag
- [ ] Per-call propagator instantiation (`TraceContextTextMapPropagator()` inside inject/extract bodies)
- [ ] Spans in hot loops without sampling guards
- [ ] Exceptions silently swallowed after `record_exception` (should still raise or handle explicitly)
- [ ] Using `SimpleSpanProcessor` in production (blocks on every span)
- [ ] Jaeger exporter (removed in v1.22; use OTLP to Jaeger backend instead)

3. **Generate report** with:
   - Current state assessment (what's instrumented, how)
   - Correctness issues (broken propagation, wrong status codes, PII leaks)
   - Performance issues (SimpleSpanProcessor in prod, hot-loop spans, unbounded queues)
   - Production-readiness gaps (shutdown, sampling, resource attributes)
   - Priority fixes ordered by severity + effort
   - Code examples for each recommendation

## Synergies

- Deep propagator / custom transport patterns -> `opentelemetry:otel-architect` (agent)
- Async context propagation patterns -> `python-development:async-python-patterns`
- RabbitMQ propagation -> `messaging:rabbitmq-expert` + `opentelemetry:opentelemetry` reference
