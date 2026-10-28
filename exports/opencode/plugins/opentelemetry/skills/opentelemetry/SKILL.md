---
name: opentelemetry
description: >
  Knowledge base for OTel in Python: async gotchas, non-HTTP transports, production patterns.
  TRIGGER WHEN: working with OpenTelemetry, distributed tracing, span instrumentation, context propagation, OTLP exporters, sampling strategies, or observability pipelines.
---

<daodan_host_binding host="opencode">
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

OpenCode V2 binding: repository reads use read/glob/grep, writes use write/edit/patch,
shell execution uses shell, network fetch uses webfetch, network search uses
websearch, and a user question uses the registered question tool. shell takes command, optional workdir, timeout
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

# OpenTelemetry Python

Index for OTel Python -- traces, metrics, log-trace correlation, distributed propagation. References hold the gotchas; canonical reference lives at https://opentelemetry-python.readthedocs.io and https://opentelemetry.io/docs/.

## When to use

- New Python service that needs distributed tracing
- Adding OTel to FastAPI / Celery / async Python
- Custom transports (AMQP, ZMQ, Kafka) needing propagator wiring
- OTLP exporter / Collector / AWS ADOT configuration
- Auditing existing instrumentation for gaps or anti-patterns
- Log-trace correlation
- Sampling strategy choice for production

## Quick-start production recipe

For most Python services, start with this and iterate:

1. **Init**: `opentelemetry-bootstrap -a install` + `opentelemetry-instrument` wrapper
2. **Resource**: set `service.name`, `service.version`, `deployment.environment`
3. **Sampler**: `ParentBased(TraceIdRatioBased(0.1))` -- 10% head sampling
4. **Exporter**: OTLP gRPC to a local Collector at `localhost:4317`
5. **Processor**: `BatchSpanProcessor` with default tuning (raise `OTEL_BSP_MAX_QUEUE_SIZE=8192` if bursty)
6. **Shutdown**: register `provider.shutdown()` in lifespan / `atexit` / `SIGTERM`

Then escalate based on what you actually need:
- Custom business spans → manual `tracer.start_as_current_span()`
- Non-HTTP transport → custom propagator (skeleton in `exporters-and-backends.md`)
- AWS deployment → ADOT distro + X-Ray ID generator (`aws-deployment.md`)
- High throughput → tune BSP queue size + export timeout
- Error-only retention → tail sampling at the Collector

## Auto vs manual instrumentation (the matrix)

| Layer | Approach | Examples |
|-------|----------|----------|
| HTTP frameworks | **Auto** | FastAPI, Django, Flask |
| Database clients | **Auto** | SQLAlchemy, psycopg2, asyncpg |
| HTTP clients | **Auto** | httpx, requests, aiohttp |
| Message queues | **Auto** | Celery, Kafka |
| Cache | **Auto** | redis, memcached |
| Business logic | **Manual** | Order processing, payment flows |
| Custom transport | **Manual** | AMQP payload, ZMQ events |

Combined pattern: `opentelemetry-instrument` wraps the app for auto; manual spans inside routes/handlers for business logic. See `instrumentation-patterns.md` for per-framework details.

## Critical framework gotchas (worth memorizing)

- **Celery**: init OTel **after fork** via `@worker_process_init.connect`. `BatchSpanProcessor` threads don't survive `fork()` -- export silently fails otherwise. Recipe in `instrumentation-patterns.md`.
- **SQLAlchemy async**: pass `engine.sync_engine` to the instrumentor, NOT the async engine.
- **FastAPI**: register `provider.shutdown()` in `lifespan` cleanup, otherwise last span batch is lost on every restart.
- **HTTP status / Span Status**: only 5xx → `StatusCode.ERROR`. 4xx are client errors, leave UNSET. Business rejections (declined payment) use `add_event`, not ERROR.

## Custom transport propagation (skeleton)

For AMQP, ZMQ, custom sockets -- inject on producer, extract on consumer, use W3C TraceContext format.

```python
# Producer
from opentelemetry.propagate import inject
headers = {}; inject(headers)
message.payload["_trace_context"] = headers

# Consumer
from opentelemetry.propagate import extract
from opentelemetry import context, trace
ctx = extract(carrier=message.payload.get("_trace_context", {}))
token = context.attach(ctx)
try:
    with trace.get_tracer(__name__).start_as_current_span("process"):
        handle(message)
finally:
    context.detach(token)
```

Full discussion + custom SpanProcessor patterns: `exporters-and-backends.md`.

## Sampling -- the decision tree

- **`ParentBased(TraceIdRatioBased(rate))`** -- the right default. Respects upstream decision; only applies the delegate to root spans. Without ParentBased, downstream services re-roll → broken traces.
- **Tail sampling at the Collector** -- when you need to keep 100% of errors/slow traces while sampling routine traffic. Requires trace-ID affinity (loadbalancing exporter in front).
- **Hybrid** at scale: head-sample 10-20% in SDK + tail-sample at Collector for error/slow retention.

Env shortcut: `OTEL_TRACES_SAMPLER=parentbased_traceidratio`, `OTEL_TRACES_SAMPLER_ARG=0.1`.

## Reference index

- `async-context-propagation.md` -- contextvars mechanics, asyncio task propagation, **thread boundary trap, TracedThreadPoolExecutor, fork+BSP loss, Python 3.12+ improvements** (the crown jewel of this skill -- read first when debugging missing/broken context)
- `instrumentation-patterns.md` -- auto-instrument setup, FastAPI/Celery/SQLAlchemy patterns, `traced_async` decorator, `TracedClass` mixin, sensitive-arg redaction, error handling
- `exporters-and-backends.md` -- OTLP gRPC vs HTTP, BSP tuning, propagation formats, custom SpanProcessors, multi-backend Collector YAML
- `aws-deployment.md` -- ADOT distro, X-Ray ID generator + propagator, ECS sidecar with memory_limiter ordering, IAM list, Lambda layer, collector-less when/when-not, X-Ray SDK migration
- `production-checklist.md` -- do/don't operational rules, resource detection boilerplate, signal maturity, version pinning policy

## Three pillars correlation (one-liner)

```python
# Inject trace_id / span_id / service_name into every stdlib log record
from opentelemetry.instrumentation.logging import LoggingInstrumentor
LoggingInstrumentor().instrument(set_logging_format=True)
# OR env: OTEL_PYTHON_LOG_CORRELATION=true
```

For metrics: `MeterProvider` + `Counter`/`Histogram`/`UpDownCounter`/`ObservableGauge`. Shares `Resource` with `TracerProvider` so service identity is consistent.

For OTLP log export: the Logs SDK (`opentelemetry._logs`, leading underscore = experimental) -- in production today, use the `LoggingInstrumentor` bridge and ship via your existing log pipeline.

## Official docs

- Python SDK: https://opentelemetry-python.readthedocs.io/
- Specification: https://opentelemetry.io/docs/specs/otel/
- All instrumentations index: https://github.com/open-telemetry/opentelemetry-python-contrib/tree/main/instrumentation
- Collector contrib: https://github.com/open-telemetry/opentelemetry-collector-contrib
- Release notes (always check before upgrade): https://github.com/open-telemetry/opentelemetry-python/releases
