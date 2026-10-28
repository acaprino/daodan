<daodan_host_binding host="claude">
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

Claude binding: repository read, file discovery and content search use Read, Glob
and Grep; repository write and repository edit use Write and Edit; shell execution
uses Bash; network fetch uses WebFetch and network search uses WebSearch; a user
question uses AskUserQuestion. Pass the executable string in Bash's
command field, and use its registered timeout/background schema. Worker dispatch
uses the available native Agent mechanism and its registered agent-selection and
prompt fields. Do not turn a prose role label into an invented role argument.
Inherit the session model unless the declared workflow and active schema permit an
override. Load installed skills by qualified ID; named roles use their owning
plugin's agent identity, while workflow entries use /<plugin>:<workflow>.
Required foreign providers use Claude's marketplace/install commands:
claude plugin marketplace add <source>, then claude plugin install <provider>@<marketplace>.
A provider that is installed but disabled is enabled with
claude plugin enable <provider>@<marketplace>; check `claude plugin list --json`
before the first phase, and stop with that command when any plugin of this
package's dependency closure, direct or transitive, is off.
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

# Exporters and Backends

OTLP transport choice, BatchSpanProcessor tuning, propagation formats, custom SpanProcessors, Collector pipelines, three-pillars correlation. The protocol/format/sampler details live upstream; this file is the production gotchas + the composite local patterns.

## When to use

Wiring an SDK to a Collector or backend, picking a propagator, writing a custom SpanProcessor for filtering/enrichment, or designing a multi-backend Collector pipeline. For per-framework instrumentation (FastAPI, Celery, SQLAlchemy), see `instrumentation-patterns.md`.

## OTLP gRPC vs HTTP -- the choice that matters

| Factor | gRPC (port 4317) | HTTP/protobuf (port 4318) |
|--------|------------------|---------------------------|
| Throughput | 10-50k spans/sec | 5-20k spans/sec |
| Load balancing | Needs gRPC-aware LB | Standard ALB/nginx works |
| Debugging | Binary | curl-friendly |
| Serverless | Poor (persistent conn cost) | **Preferred** (stateless) |
| Firewall friendliness | Often blocked | Generally allowed |

Rule of thumb: **gRPC for high-throughput services in K8s where you control the network; HTTP/protobuf for Lambda, anything behind an ALB, or restricted firewalls.** The OTel spec now defaults to `http/protobuf`.

## Gotchas

- **`BatchSpanProcessor` queue overflow is silent by default.** When the queue fills (default 2048), new spans are dropped with no error/warning. Monitor `otel.bsp.spans.dropped` (if available in your SDK version) or set `OTEL_LOG_LEVEL=debug`. Tune `OTEL_BSP_MAX_QUEUE_SIZE=8192` for spiky workloads.
- **`SimpleSpanProcessor` blocks every coroutine on every `span.end()`.** Useful in tests only -- catastrophic in production. `BatchSpanProcessor` runs the exporter on a background thread independent of the asyncio loop.
- **`max_export_batch_size` > 512 risks export timeouts.** Most backends accept up to ~512 spans per batch comfortably; larger batches increase per-export latency.
- **`export_timeout_millis=30000` blocks shutdown** for 30s if the exporter hangs. Reduce to 5-10s if your shutdown SLA is tight; raise to 60s if Collector is remote/under load.
- **Propagator order matters on extract**, not on inject. The composite tries each propagator in order; first match wins. On inject, ALL propagators write their headers -- outgoing requests carry every format.
- **For non-HTTP transports, never mix trace context with business data in the carrier.** Use a namespaced key like `"_trace_context"` to avoid collision.
- **Tail sampling at the Collector requires trace-ID affinity.** Use the `loadbalancing` exporter in a first-tier Collector to route all spans of a trace to the same second-tier instance, otherwise tail decisions see partial traces.
- **`memory_limiter` MUST be the first processor in every Collector pipeline** -- it prevents OOM by dropping data under memory pressure. After-the-fact ordering will OOM under spike.
- **Logs SDK is still experimental** (the `_logs` underscore is intentional). Use `LoggingInstrumentor` to bridge to stdlib logs in production today; adopt OTLP log export when the API stabilizes.

## BatchSpanProcessor tuning (the parameters worth knowing)

| Param | Env var | Default | When to change |
|-------|---------|---------|----------------|
| `max_queue_size` | `OTEL_BSP_MAX_QUEUE_SIZE` | 2048 | Bursty workloads → 4096-8192 |
| `schedule_delay_millis` | `OTEL_BSP_SCHEDULE_DELAY` | 5000 | Near-realtime → 1000-2000 |
| `max_export_batch_size` | `OTEL_BSP_MAX_EXPORT_BATCH_SIZE` | 512 | Match exporter limits; rarely raise |
| `export_timeout_millis` | `OTEL_BSP_EXPORT_TIMEOUT` | 30000 | Tight shutdown → 5000; remote Collector → 60000 |

## Propagators (which header(s) to use)

| Format | Headers | When |
|--------|---------|------|
| **W3C TraceContext** | `traceparent`, `tracestate` | Default for new systems |
| **W3C Baggage** | `baggage` | Cross-service metadata (tenant_id, feature flags) |
| **B3** | `b3` or `X-B3-*` | Legacy Zipkin, older Istio/Envoy |
| **AWS X-Ray** | `X-Amzn-Trace-Id` | AWS-native (ALB, API GW, Lambda) |

Composite (when you need to bridge):
```python
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.trace.propagation import TraceContextTextMapPropagator
from opentelemetry.baggage.propagation import W3CBaggagePropagator
from opentelemetry.propagators.aws import AwsXRayPropagator

set_global_textmap(CompositePropagator([
    TraceContextTextMapPropagator(), W3CBaggagePropagator(), AwsXRayPropagator(),
]))
```
Or env-only: `OTEL_PROPAGATORS="tracecontext,baggage,xray"`.

## Custom transport inject/extract (the local pattern for AMQP, ZMQ, custom sockets)

For dict-based payloads where headers aren't a separate field:

```python
from opentelemetry.propagate import inject, extract
from opentelemetry import context, trace

tracer = trace.get_tracer(__name__)

# Producer
headers = {}
inject(headers)
message.payload["_trace_context"] = headers       # namespaced -- never mix with business data

# Consumer
ctx = extract(carrier=message.payload.get("_trace_context", {}))
token = context.attach(ctx)
try:
    with tracer.start_as_current_span("process_message"):
        handle(message)
finally:
    context.detach(token)
```

Kafka has `opentelemetry-instrumentation-kafka-python` for auto inject/extract -- only roll your own for transports without an official instrumentation.

## Custom SpanProcessor (the filtering+enrichment pattern)

Drops health-check noise and adds deployment metadata before the batch processor sees the span:

```python
from opentelemetry.sdk.trace import SpanProcessor, ReadableSpan

class FilteringEnrichmentProcessor(SpanProcessor):
    """Drops health-check spans and enriches all others."""
    def __init__(self, next_processor, drop_names: set[str]):
        self._next = next_processor
        self._drop_names = drop_names

    def on_start(self, span, parent_context=None):
        span.set_attribute("deployment.region", "us-east-1")
        self._next.on_start(span, parent_context)

    def on_end(self, span: ReadableSpan):
        if span.name in self._drop_names: return
        if span.attributes and span.attributes.get("http.target") in ("/healthz", "/ready"): return
        self._next.on_end(span)

    def shutdown(self, timeout_millis=30000): self._next.shutdown(timeout_millis)
    def force_flush(self, timeout_millis=30000): self._next.force_flush(timeout_millis)

# Wire it up
batch = BatchSpanProcessor(OTLPSpanExporter(endpoint="http://collector:4317"))
provider.add_span_processor(FilteringEnrichmentProcessor(batch, {"health-check", "readiness"}))
```

Processors chain by order added; if your filter drops a span, the batch exporter never sees it -- this reduces export volume without changing sampling.

## Multi-backend Collector pipeline (the local YAML worth keeping)

Routes traces to X-Ray AND Jaeger, metrics to CloudWatch EMF, from a single OTLP receiver:

```yaml
receivers:
  otlp:
    protocols:
      grpc: { endpoint: 0.0.0.0:4317 }
      http: { endpoint: 0.0.0.0:4318 }

processors:
  batch: { timeout: 5s, send_batch_size: 256 }
  memory_limiter: { check_interval: 1s, limit_mib: 400, spike_limit_mib: 100 }
  resourcedetection: { detectors: [env, ec2, ecs], timeout: 5s, override: false }

exporters:
  awsxray: { region: us-east-1, indexed_attributes: [otel.resource.service.name] }
  awsemf:  { region: us-east-1, namespace: MyApplication, log_group_name: /aws/otel/metrics }
  otlp/jaeger: { endpoint: jaeger:4317, tls: { insecure: true } }

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, resourcedetection, batch]
      exporters: [awsxray]
    traces/jaeger:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [otlp/jaeger]
    metrics:
      receivers: [otlp]
      processors: [memory_limiter, resourcedetection, batch]
      exporters: [awsemf]
```

Why this shape:
- `memory_limiter` first, always.
- Named exporters (`otlp/jaeger`) disambiguate when you have multiple instances of the same exporter type.
- Multiple pipelines = multi-backend routing from one receiver.
- `resourcedetection: override: false` so application-set Resource attributes win.

## Sampling pointer

For sampler design (head, tail, hybrid, ParentBased nuances) see the SKILL.md "Sampling Strategies" section -- it's compact and lives there because it crosses every component.

## Three pillars correlation (the production-today recipe)

```python
# Log-trace correlation via stdlib logging
from opentelemetry.instrumentation.logging import LoggingInstrumentor
LoggingInstrumentor().instrument(set_logging_format=True)
# OR env var: OTEL_PYTHON_LOG_CORRELATION=true
```

Injects `otelTraceID`, `otelSpanID`, `otelServiceName` into every log record. For structured JSON logging, write a `logging.Filter` that pulls `trace.get_current_span().get_span_context()` -- skeleton in the upstream docs.

## Official docs

- OTLP spec: https://opentelemetry.io/docs/specs/otlp/
- Python SDK exporters: https://opentelemetry-python.readthedocs.io/en/stable/sdk/trace.export.html
- BatchSpanProcessor reference: https://opentelemetry-python.readthedocs.io/en/stable/sdk/trace.export.html#opentelemetry.sdk.trace.export.BatchSpanProcessor
- W3C TraceContext: https://www.w3.org/TR/trace-context/
- W3C Baggage: https://www.w3.org/TR/baggage/
- B3 propagation: https://github.com/openzipkin/b3-propagation
- AWS X-Ray propagator: https://github.com/open-telemetry/opentelemetry-python-contrib/tree/main/propagator/opentelemetry-propagator-aws-xray
- Tail sampling processor: https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/processor/tailsamplingprocessor
- Loadbalancing exporter (trace-ID affinity): https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/exporter/loadbalancingexporter
- Logs SDK status: https://github.com/open-telemetry/opentelemetry-python/blob/main/docs-requirements.txt (track `opentelemetry._logs` API)

## Related

- `instrumentation-patterns.md` -- the per-framework setup that produces the spans
- `production-checklist.md` -- the do/don't rules this file's defaults derive from
- `aws-deployment.md` -- ADOT-specific extensions (X-Ray, AWS resource detectors)
- `async-context-propagation.md` -- thread / fork / asyncio context traps
