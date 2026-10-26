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

# Production Checklist

The do/don't rules and operational defaults for shipping OTel Python in production. Most of the version-specific detail (package versions, breaking changes per release) lives upstream and changes every minor release -- check the links below.

## When to use

Auditing a service for production-readiness, or before a first prod deploy. For instrumentation patterns (FastAPI, Celery, SQLAlchemy), see `instrumentation-patterns.md`.

## Do these (the non-negotiables)

1. **Always set `service.name`** -- without it everything appears as `unknown_service`. Set via `Resource.create({"service.name": "..."})` or `OTEL_SERVICE_NAME` env var (env wins).
2. **`BatchSpanProcessor` exclusively in production.** `SimpleSpanProcessor` exports synchronously per `span.end()` -- catastrophic for throughput.
3. **`ParentBased` sampling everywhere.** Mixing `ParentBased` in service A with raw `TraceIdRatioBased` in service B re-rolls sampling per-hop and produces partial traces. `ParentBased` only applies its delegate to root spans.
4. **Register shutdown handlers.** Without `provider.shutdown()` on `atexit`/`SIGTERM`, the last batch in `BatchSpanProcessor` is lost on every restart.
5. **`OTEL_SDK_DISABLED=true` as a kill switch.** Deploys with this env var return no-op for all signals -- instant rollback without code change.
6. **`span.is_recording()` before expensive attribute computation.** API guarantees no-throw on non-recording spans, but JSON-serializing a 50KB object still wastes CPU.
7. **Tune `OTEL_BSP_MAX_QUEUE_SIZE` for spiky workloads.** Default 2048; bump to 8192+ for bursts. Dropped spans are silent by default -- monitor `otel.bsp.spans.dropped` if available.

## Don't do these

1. **Don't init OTel before `fork()`** in Celery / Gunicorn prefork. `BatchSpanProcessor` threads don't survive fork. Init in `worker_process_init` (Celery) or `post_fork` (Gunicorn). See `instrumentation-patterns.md` for full Celery recipe.
2. **Don't create spans in hot loops without sampling.** Even 1µs/span × 1M iter = 1s of overhead. Move outside the loop and record iteration count as an attribute.
3. **Don't put PII or secrets in span attributes or baggage.** Baggage propagates to every downstream service. Attributes land in your tracing backend with broad read access. Scrub or hash.
4. **Don't set attributes with `None` values.** Behavior is undefined -- some exporters drop, others raise. Guard with `if value is not None`.
5. **Don't use `SimpleSpanProcessor` "just for staging."** Staging mirrors prod. Use `OTEL_LOG_LEVEL=debug` to diagnose locally.
6. **Don't skip the Collector in production.** Buffering, retry-with-backoff, attribute enrichment, tail sampling, protocol translation -- all Collector-only. SDK-direct-to-backend is dev-only.

## Resource detection (boilerplate worth pasting)

Run once at startup. Resource attributes enrich every span/metric/log.

```python
from opentelemetry.sdk.resources import (
    Resource, get_aggregated_resources,
    ProcessResourceDetector, OTELResourceDetector,
)
from opentelemetry.sdk.extension.aws.resource.ec2 import AwsEc2ResourceDetector
from opentelemetry.sdk.extension.aws.resource.ecs import AwsEcsResourceDetector

resource = get_aggregated_resources(
    detectors=[
        OTELResourceDetector(),         # OTEL_RESOURCE_ATTRIBUTES env var
        ProcessResourceDetector(),       # process.pid, process.runtime.*
        AwsEc2ResourceDetector(),        # cloud.provider, cloud.region, host.id
        AwsEcsResourceDetector(),        # aws.ecs.cluster.arn, aws.ecs.task.arn
    ],
    initial_resource=Resource.create({
        "service.name": "order-service",
        "service.version": "2.1.0",
    }),
    timeout=5,
)
```

Since SDK 1.40.0: `OTEL_EXPERIMENTAL_RESOURCE_DETECTORS=*` auto-loads all installed detectors via entry points -- no Python listing needed.

## Signal maturity (sanity check before adoption)

| Signal | Status | Production ready? |
|--------|--------|-------------------|
| Traces | Stable | **Yes** |
| Metrics | Stable | **Yes** |
| Logs | Experimental (`opentelemetry._logs`) | Use bridge instrumentation, not direct SDK |
| Baggage | Stable | **Yes** |

For log-trace correlation in production today, use `opentelemetry-instrumentation-logging` to inject `trace_id`/`span_id` into stdlib log records and ship through your existing log pipeline (CloudWatch, ELK, etc.). Adopt OTLP log export when the API stabilizes.

## Pinning policy

- **Stable** (`opentelemetry-api`, `opentelemetry-sdk`, exporters): pin to **exact version** (e.g. `==1.42.1`).
- **Instrumentation packages** (e.g. `opentelemetry-instrumentation-fastapi==0.63b1`): pin with `~=` to allow patch updates.
- Track upstream release notes -- minor versions occasionally break instrumentation when the underlying library changes its internals.

## Official docs

- Python SDK GitHub: https://github.com/open-telemetry/opentelemetry-python
- Python contrib (instrumentations): https://github.com/open-telemetry/opentelemetry-python-contrib
- Python SDK readthedocs: https://opentelemetry-python.readthedocs.io/
- Spec: https://opentelemetry.io/docs/specs/otel/
- Collector contrib: https://github.com/open-telemetry/opentelemetry-collector-contrib
- AWS ADOT: https://aws-otel.github.io/
- X-Ray → OTel migration: https://docs.aws.amazon.com/xray/latest/devguide/migrate-xray-to-opentelemetry-python.html
- Release notes (check before any upgrade): https://github.com/open-telemetry/opentelemetry-python/releases

## Related

- `instrumentation-patterns.md` -- per-framework setup, decorators, error handling
- `exporters-and-backends.md` -- BSP tuning details, propagation formats, custom processors
- `aws-deployment.md` -- ADOT, X-Ray, ECS sidecar, collector-less direct export
- `async-context-propagation.md` -- the crown jewel: thread/fork/asyncio context traps
