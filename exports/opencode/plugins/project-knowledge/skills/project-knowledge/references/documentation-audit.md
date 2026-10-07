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
