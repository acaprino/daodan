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

# Instrumentation Patterns

Per-framework setup (FastAPI, Celery, SQLAlchemy async, HTTP clients), custom decorators (`traced_async`, `TracedClass` mixin), error-handling rules, and the Celery-after-fork recipe that catches everyone the first time.

## When to use

Adding OTel to a new service, or auditing an existing one for missing/wrong instrumentation. For exporter/Collector configuration, see `exporters-and-backends.md`.

## Auto-instrumentation in 3 commands

```bash
pip install opentelemetry-distro opentelemetry-exporter-otlp
opentelemetry-bootstrap -a install                  # scans installed packages
opentelemetry-instrument uvicorn main:app           # wraps your entry point
```

This sets a global TracerProvider/MeterProvider with W3C TraceContext propagation. Typical overhead: < 1% CPU.

## Key environment variables

| Variable | Purpose |
|----------|---------|
| `OTEL_SERVICE_NAME` | Service identity (mandatory) |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Collector address (e.g. `http://collector:4317`) |
| `OTEL_TRACES_SAMPLER` | `parentbased_traceidratio` is the right default |
| `OTEL_TRACES_SAMPLER_ARG` | Sample rate (e.g. `0.1`) |
| `OTEL_PYTHON_DISABLED_INSTRUMENTATIONS` | Comma-separated libs to skip |
| `OTEL_PYTHON_FASTAPI_EXCLUDED_URLS` | Regex for routes to skip (e.g. `health,ready,metrics`) |
| `OTEL_SDK_DISABLED` | Emergency kill switch |

## Gotchas

- **Celery + `BatchSpanProcessor` + `fork()` = silent telemetry loss** unless OTel is initialized in the `worker_process_init` signal. The BSP background thread doesn't survive fork. This is the #1 production OTel bug. See recipe below.
- **SQLAlchemy async needs `.sync_engine`** passed to the instrumentor, not the async engine. The instrumentation patches the synchronous interface that asyncpg wraps internally:
  ```python
  SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine, enable_commenter=True)
  ```
  `enable_commenter=True` injects trace context as SQL comments → DB log correlation.
- **FastAPI lifespan must call `provider.shutdown()`** in the cleanup branch. Without it, the last batch of spans is lost on every restart/deploy.
- **Don't set `OK` on every span.** `UNSET` is the correct default for successful operations. Only the outermost boundary (HTTP server handler when the request completes) SHOULD set `OK`. Setting OK in nested spans prevents parents from later transitioning to ERROR.
- **Business-logic rejections (declined payment, validation failure) use `add_event`, not `StatusCode.ERROR`.** `ERROR` is for infrastructure failures (5xx, gateway timeouts, exceptions). Mixing them poisons your error rate metrics.
- **`record_exception()` creates a span event** with type/message/stacktrace -- it does NOT set ERROR status by itself. `start_as_current_span()` defaults `record_exception=True` AND `set_status_on_exception=True`, so unhandled exceptions auto-mark ERROR; if you catch and re-raise, you must set status manually.
- **Disconnected traces in Celery** have three usual causes: (a) OTel initialized before fork, (b) `CeleryInstrumentor` only on producer or only on consumer, (c) task dispatched outside an active span context.
- **Don't put high-cardinality values (user IDs, request bodies) in span names.** Use attributes. Span names should have low cardinality so backends can aggregate.

## FastAPI production setup

```python
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

resource = Resource.create({
    "service.name": "order-api",
    "service.version": os.getenv("APP_VERSION", "0.0.0"),
    "deployment.environment": os.getenv("ENVIRONMENT", "production"),
})
provider = TracerProvider(resource=resource, sampler=ParentBased(TraceIdRatioBased(0.1)))
provider.add_span_processor(BatchSpanProcessor(
    OTLPSpanExporter(endpoint="http://collector:4317", insecure=True),
    max_queue_size=4096,
))
trace.set_tracer_provider(provider)

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    provider.shutdown()

app = FastAPI(title="Order API", lifespan=lifespan)
FastAPIInstrumentor.instrument_app(app, excluded_urls="health,ready,metrics")
```

Custom request-scoped attributes via `server_request_hook=` to capture `x-request-id`, tenant headers, etc.

## Celery: the after-fork recipe (memorize this)

**Producer side** -- safe at module level:
```python
from opentelemetry.instrumentation.celery import CeleryInstrumentor
CeleryInstrumentor().instrument()
```

**Consumer side** -- init OTel inside the signal, AFTER fork:
```python
from celery import Celery
from celery.signals import worker_process_init

app = Celery("tasks", broker="redis://localhost:6379/0")

@worker_process_init.connect(weak=False)
def init_worker_tracing(**kwargs):
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.instrumentation.celery import CeleryInstrumentor

    provider = TracerProvider(resource=Resource.create({"service.name": "celery-worker"}))
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(insecure=True)))
    trace.set_tracer_provider(provider)
    CeleryInstrumentor().instrument()
```

How context propagation works under the hood: `before_task_publish` injects context into message headers; `task_prerun` extracts and creates the child span. Result: FastAPI → Celery task → downstream service appears as one distributed trace.

For Gunicorn prefork the equivalent hook is `post_fork` in `gunicorn.conf.py`.

## SQLAlchemy async (the single gotcha)

```python
from sqlalchemy.ext.asyncio import create_async_engine
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

engine = create_async_engine("postgresql+asyncpg://user:pass@db/orders")
SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine, enable_commenter=True)
# Generated SQL: SELECT * FROM orders /* traceparent='00-abc...' */
```

## HTTP clients

```python
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
HTTPXClientInstrumentor().instrument()
```

Equivalents: `opentelemetry-instrumentation-requests`, `opentelemetry-instrumentation-aiohttp-client`. All inject `traceparent` automatically into outgoing requests.

## Custom decorators (the local IP)

### `@traced_async` with argument extraction

```python
import inspect, functools
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

def traced_async(name, extract_args=None):
    """Wraps an async function in a span; optionally captures arguments."""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            tracer = trace.get_tracer(func.__module__)
            with tracer.start_as_current_span(name) as span:
                if extract_args and span.is_recording():
                    sig = inspect.signature(func)
                    bound = sig.bind(*args, **kwargs); bound.apply_defaults()
                    for arg_name in extract_args:
                        v = bound.arguments.get(arg_name)
                        if v is not None:
                            span.set_attribute(f"app.{arg_name}", redact_value(arg_name, v))
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise
        return wrapper
    return decorator

@traced_async("evaluate_signal", extract_args=["symbol", "timeframe"])
async def evaluate_signal(symbol: str, timeframe: str, tick: dict): ...
```

### `TracedClass` mixin (auto-wraps every public async method)

```python
class TracedClass:
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        for name, method in inspect.getmembers(cls, predicate=inspect.iscoroutinefunction):
            if not name.startswith("_"):
                setattr(cls, name, traced_async(f"{cls.__name__}.{name}")(method))
```

### Sensitive-arg redaction (paste-ready)

```python
SENSITIVE_KEYS = {"password", "token", "api_key", "secret", "credential"}

def redact_value(key: str, value) -> str:
    if any(s in key.lower() for s in SENSITIVE_KEYS):
        return "[REDACTED]"
    return str(value)
```

## Error handling: infrastructure vs business logic

```python
from opentelemetry.trace import Status, StatusCode

with tracer.start_as_current_span("process_payment") as span:
    span.set_attribute("payment.amount", payment.amount)
    try:
        result = await gateway.charge(payment)
        # leave UNSET on success -- only outermost handlers set OK
        return result
    except GatewayTimeoutError as e:                     # infrastructure
        span.record_exception(e, attributes={"error.category": "gateway_timeout"})
        span.set_status(Status(StatusCode.ERROR, f"Gateway timeout: {e}"))
        raise
    except InsufficientFundsError as e:                  # business outcome
        span.add_event("payment_declined", attributes={"reason": str(e)})
        return {"status": "declined"}
```

Status transitions: `UNSET` → `OK` or `UNSET` → `ERROR`. **Once set, never transitions back.** For HTTP spans: only 5xx → `ERROR`; 4xx are client errors, leave UNSET.

## Official docs

- Auto-instrumentation: https://opentelemetry.io/docs/zero-code/python/
- FastAPI instrumentation: https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation/fastapi/fastapi.html
- Celery instrumentation: https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation/celery/celery.html
- SQLAlchemy instrumentation: https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation/sqlalchemy/sqlalchemy.html
- httpx instrumentation: https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation/httpx/httpx.html
- Span Status semantic conventions: https://opentelemetry.io/docs/specs/otel/trace/api/#set-status
- All instrumentations index: https://github.com/open-telemetry/opentelemetry-python-contrib/tree/main/instrumentation

## Related

- `production-checklist.md` -- shutdown hooks, kill switch, span.is_recording()
- `exporters-and-backends.md` -- Collector pipelines, BSP tuning, propagators
- `async-context-propagation.md` -- thread/fork/asyncio context (Celery prefork lives there too)
- `aws-deployment.md` -- ADOT distro, X-Ray, ECS sidecar, Lambda layers
