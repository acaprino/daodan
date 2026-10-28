<daodan_host_binding host="codex">
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

Codex binding: the adapter binds repository read to read_file, writes to
apply_patch and shell execution to shell; use the equivalent registered tools of
the active Codex runtime and their actual fields. Network search and network fetch
use the runtime's registered web search tool when the Codex configuration enables
it. A user question uses the runtime's registered question tool when one exists;
otherwise ask it in the reply and wait for the answer. In particular, a shell example's
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

# Infrastructure: Monoliths, Databases, CI/CD, and Feature Flags

## Monolith vs Microservices

### MUST

- **Start with a monolith or modular monolith** unless you have a proven, specific need for microservices. Martin Fowler's MonolithFirst principle: almost all successful microservice stories started with a monolith that outgrew its architecture.

### Case Studies

- **Segment:** migrated to microservices then back to a monolith because premature decomposition drowned them in complexity.
- **Amazon Prime Video (2023):** migrated a monitoring service from microservices back to a monolith, achieving 90% cost reduction.
- **Shopify:** runs one of the largest Rails monoliths (3M+ lines of code) successfully using a modular architecture.

### DO

- Build a modular monolith with clear module boundaries using Domain-Driven Design.
- Move to microservices when: 50+ engineers need team autonomy, components have genuinely different scaling requirements today, deployment coordination is a bottleneck, or regulatory requirements demand physical separation.
- Use the Strangler Fig pattern for gradual migration.

### DON'T

- Create a "distributed monolith" -- services so tightly coupled they deploy in lockstep.
- Split by technical layers (API service, data service) -- split by business capabilities.

## Database Access

### MUST

- **Always place an API layer between clients and the database.** Direct database connections from SPAs, mobile apps, or desktop clients are a critical security vulnerability.
- **Use connection pooling** in production. Creating new connections per request costs ~150ms overhead; a pool reduces this to <1ms. Documented improvement: response time from 150ms to 12ms.
- **Prevent N+1 queries** -- the most common ORM performance killer. 100 blog posts with authors generates 101 queries instead of 2.

### DO

- Use eager loading (`select_related`/`prefetch_related` in Django, `JOIN FETCH` in JPA, `.Include()` in EF) and DataLoader for GraphQL, Bullet for Ruby, Sentry for production detection.
- Set query count budgets -- list page: 2-5 queries, detail page: 1-3.
- Write tests asserting query counts.
- Use read replicas for read-heavy workloads and DTOs/projections for read endpoints.

## CI/CD Pipelines

### MUST

- **Automate all builds, tests, and deployments.** Knight Capital's manual deployment process directly contributed to their $440 million loss in 45 minutes.
- Run automated tests as a pipeline gate.
- Sign artifacts securely -- store signing keys in CI secrets management, never in source code.

### Platform Build Chains

| Platform | Pipeline |
|----------|---------|
| **SPA/PWA** | Vite/Webpack to lint to unit tests to E2E (Playwright/Cypress) to CDN deploy |
| **Android** | Gradle to Fastlane to Play Store |
| **iOS** | macOS runners + Xcode to Fastlane Match to TestFlight |
| **Electron** | electron-builder for cross-platform packaging |
| **Tauri** | `cargo tauri build` with Rust compilation (cache with `swatinem/rust-cache`) |

Mobile apps face 1-3 day App Store review cycles -- you can't "hotfix" like web.

## Environment Separation

### MUST

- **Maintain separate dev/staging/prod environments** with distinct configurations, databases, and API keys.
- Never use production data in development without anonymization.
- Use environment variables for all environment-specific settings (12-Factor App methodology).
- Use versioned database migrations (Flyway, Alembic, Prisma Migrate) run as a separate CI step.

## Observability

### MUST

- **Use structured logging (JSON format)** with consistent fields: `timestamp`, `level`, `message`, `request_id`, `user_id`, `trace_id`.
- Implement error tracking from day one -- Sentry (cross-platform), Firebase Crashlytics (mobile).
- Include correlation/trace IDs in every log entry.

### DO

- Follow the three pillars: Logs (ELK Stack, Grafana Loki), Metrics (Prometheus + Grafana), Traces (OpenTelemetry to Jaeger/Zipkin).
- Use OpenTelemetry as the instrumentation standard to avoid vendor lock-in.

### DON'T

- Log sensitive data (passwords, tokens, PII) -- creates compliance violations.
- Rely on `console.log` in production.

## Feature Flags

### MUST

- **Never reuse a feature flag.** Knight Capital repurposed a flag from 2003 for a 2012 feature. One of eight servers didn't receive the update, the old flag triggered legacy test code that bought high and sold low at maximum speed. In 45 minutes, they lost $440 million and went bankrupt. The SEC report documents this as a direct consequence of flag reuse and dead code.
- **Feature flags must have short lifespans.** Remove flags and associated dead code after rollout is complete.
- **Implement kill switches** -- the ability to instantly disable a feature without redeployment.
- Use role-based access control for flag management.

### Platform Rollout Mechanisms

| Platform | Mechanism |
|----------|----------|
| **SPA/PWA** | Instant percentage rollouts via LaunchDarkly/Statsig/Unleash |
| **Mobile** | Google Play staged rollout (1% to 5% to 20% to 100%) or App Store phased release |
| **Desktop** | Update channels (stable/beta/canary) plus in-app flags |

Always configure fallback/default values when the flag service is unreachable.
