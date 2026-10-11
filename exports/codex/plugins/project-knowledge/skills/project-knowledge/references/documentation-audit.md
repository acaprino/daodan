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

# Documentation audit method

## Inputs and read-only boundary

Receive scope, revision/snapshot, document paths, selected dimensions, intended
audience, authorized mode, evidence paths and report destination. Audit-only
allows a report under the owned run; it never edits source, durable documents,
links, instruction files or ignore rules. A missing planned input is a delivery
gap, not an empty successful report.

Read the documents, their inbound links and the implementation they describe.
Search callers and relevant untouched documents when a renamed or changed concept
can invalidate them. Respect documentation frameworks and generated-file owners.
Report missing documents, duplication, broken links, stale examples and orphaned
pages as leads. Unlinked or old material is not thereby obsolete.

## Per-dimension drift

Use the selected dimensions below to compare added, removed, renamed, retyped and
signature-changed items. Each discrepancy cites the document and implementation
locator. For domain intent and design rationale, also cite an approved requirement
or decision. Code shows what is implemented; it cannot settle what was intended.

| Dimension | Implementation evidence | Drift the audit reports |
|---|---|---|
| `interfaces` | Route definitions (FastAPI/Express/Spring/Django/Rails/Gin), CLI entry points (argparse, click, commander, clap), library `__all__` / public exports, GraphQL SDL, gRPC `.proto`, emitted events (Kafka topics, RabbitMQ exchanges, webhook payloads) | Endpoint added/removed, method/path changed, request or response schema changed, auth requirement changed, CLI flag added/removed, emitted event renamed or payload changed |
| `config` | Reads of `os.environ` / `process.env` / `viper`, dotenv templates, config file schemas, feature flag SDK calls | Env var added/removed/renamed, default changed, required vs optional flip, feature flag added/removed |
| `integrations` | HTTP client calls to external hosts, webhook handlers, scheduled jobs (cron, APScheduler, BullMQ, Celery), message queue producers/consumers | External API endpoint changed, new outbound dependency, webhook signature changed, cron schedule changed, queue topic renamed |
| `architecture` | Module structure, package boundaries, dependency direction | New layer introduced, boundary violation now in code, component split or merged |
| `data-model` | ORM models (SQLAlchemy, Django ORM, Prisma, Drizzle, TypeORM, Sequelize, ActiveRecord, GORM, Diesel), Pydantic/Zod/dataclass, `CREATE TABLE`, migration files (Alembic, Flyway, Liquibase, Prisma migrate, knex) | Entity added/removed/renamed, field added/removed/renamed, type changed, nullable flipped, default changed, FK or relationship changed, index added/removed |
| `data-flows` | Call sites between components, queue producers/consumers, event bus subscriptions, pipeline DAGs (Airflow, Prefect, Dagster) | New flow path, removed/short-circuited path, new fan-out, ordering or transaction boundary changed |
| `state-machines` | Explicit FSM libs (xstate, transitions, statelessLib), enum-driven status fields with guarded transitions | State added/removed/renamed, transition added/removed, guard changed, terminal state changed |
| `dependencies` | Package manifests (package.json, pyproject.toml, Cargo.toml, go.mod, pom.xml, build.gradle, Gemfile) + lockfiles + actual imports | Dependency added/removed, version upgraded across major/minor, new optional dep, dep moved from prod to dev, unused dep, undeclared dep used |
| `concurrency` | Worker definitions, scheduler config, async runtime usage, lock primitives, idempotency keys | Worker added/removed, queue topology changed, schedule changed, locking changed, retry/backoff policy changed |
| `glossary` | Domain types, enum names, value objects, repeated terminology in models/services | Term renamed, term removed from code, new term used in code but absent from glossary |
| `auth` | Auth middleware, JWT/session config, RBAC tables, permission decorators, secret loaders | New role/permission, removed role, scope change, secret source changed, MFA path added/removed |
| `errors` | Exception classes, error code enums, retry decorators, circuit-breaker config, idempotency keys | Error code added/removed/renumbered, retry policy changed, new circuit breaker, idempotency boundary changed |
| `observability` | Logger calls with structured fields, metrics registrations (Prometheus/StatsD/OTel), tracer spans, alert rules | Metric added/removed/renamed, log field renamed, span name changed, alert added/removed |
| `deployment` | Dockerfile, compose, k8s manifests, Helm charts, Terraform, CI workflows | Image base changed, exposed port changed, env injection changed, healthcheck changed, new pipeline stage, runner changed |
| `testing` | Test directory structure, coverage config, fixtures, mocks | New test layer, removed suite, coverage thresholds changed, fixture/mock signature changed |
| `build-release` | Version files, changelog generators, release scripts | Version scheme changed, release pipeline changed, hot-fix branch convention changed |
| `migrations` | Migration history, deprecated APIs still referenced, `@deprecated` markers | New breaking change not in migration guide, deprecated API removed, upgrade step now obsolete |
| `performance` | Benchmark scripts, load test configs, code-level perf budgets, SLO config | SLO changed, benchmark removed, perf budget added/changed |
| `compliance` | Annotated PII fields, audit log calls, retention config, encryption usage | New PII field undocumented, retention period changed, encryption algorithm changed |
| `component` | Single module/class under review | Public API signature changed, internal helper now public or vice versa, dependency change |


## Native audit result

For each finding report id, severity, document locator, implementation/intent
evidence, evidence status, premise provenance, proposed disposition and affected
paths. State covered and uncovered dimensions, files read and unavailable checks.
Wrong prose, wrong implementation and unknown intent remain different diagnoses.
Do not invent the missing requirement or claim that inherited X-ray evidence was
derived independently. The coordinator wraps the native report without dropping
its uncertainty or provenance.
