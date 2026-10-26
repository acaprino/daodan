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

# Review Frameworks Reference

Consolidated review knowledge from senior-review agents: architect-review, failure-flow-tracer, pattern-quality-scorer.

---

## Cognitive Frameworks

### 1. Boundary Detective (Coupling & Cohesion)

- **God Modules** - file imports from 5+ distinct domains
- **Circular Dependencies** - modules importing each other
- **State Mutation** - component reaching into another component's internals
- **Layer Violations** - direct DB calls in UI/controller layer
- **Shared Mutability** - shared data structure, multiple accessors, no clear ownership

### 2. Abstraction Inspector (Interfaces & Leakage)

- **Leaky Abstractions** - implementation details (HTTP headers, SQL) in business logic
- **Stringly-Typed Code** - magic strings where enums/constants/union types belong
- **God Functions** - single function parsing + validating + transforming + persisting
- **Premature Abstraction** - interface/base class with one implementation, no foreseeable extension

### 3. Chaos Engineer (Resilience & Error Handling)

- **Silent Failures** - empty catch blocks, catch-log-swallow
- **Contextless Throws** - errors re-thrown without business context
- **Fire-and-Forget** - promises created but never awaited/caught
- **Missing Timeouts** - external HTTP/DB calls without explicit timeouts
- **Retry/Fallback** - no strategy when external dependency is down
- **Kill-Path Cleanup** - resources not cleaned via try/finally on SIGKILL/cancel
- **Persisted State Consistency** - no validity key (hash, fingerprint, version) to detect stale/corrupt state

### 4. State Auditor (Resource & Memory Management)

- **Global Mutability** - module-level let/var, static mutable fields
- **Memory Leaks** - event listeners/subscriptions without cleanup/unsubscribe
- **Unclosed Resources** - DB connections, file handles, streams without guaranteed finally
- **Unbounded Caches** - in-memory cache growing without expiration or max-size
- **Stale Closures** - event handlers capturing stale state from missing dependency arrays

---

## Failure Flow Methodology

6-phase analysis for resilience and correctness under failure conditions.

### Phase 1 - Map Persisted State

- Identify ALL persistent artifacts: DB files, cache files, output files, config/metadata, lock/PID files
- For each artifact determine: who writes, who reads, what validates, what invalidates

### Phase 2 - Simulate Kill Points

- Every `await` = potential kill point
- For each: state before, state after kill, on-resume behavior, bug assessment
- Check: partial writes, resources left open, next-run recovery

### Phase 3 - Trace Resume/Retry Logic

- What triggers resume, what is skipped, what is redone
- Assumptions about environment (same inputs, same config)
- What if assumption is wrong

### Phase 4 - Cache Invalidation Audit

- Validity key existence (hash, version, timestamp)
- Source data change detection
- Corruption detection (partial write, encoding error)
- Stale-fresh result mixing risk

### Phase 5 - Resource Lifecycle Audit

- Guaranteed cleanup (try/finally, context manager, defer)
- Error path behavior - not just happy path
- Cleanup idempotency

### Phase 6 - Async Concurrency Under Failure

- Sibling task behavior on one task's failure
- Shared mutable counter race conditions
- Progress reporting accuracy during concurrent execution
- Side effects already committed when parent is killed during gather

---

## Anti-Pattern Checklist

16 items with concrete thresholds.

| # | Anti-Pattern | Threshold / Signal |
|---|---|---|
| 1 | Empty catch block | Always CRITICAL |
| 2 | Long function | >50 lines - check SRP |
| 3 | Excessive imports | >10 imports - check for god-module |
| 4 | God objects/classes | Class doing too much - multiple unrelated responsibilities |
| 5 | Callback hell | Nested callbacks/promise chains - use async/await |
| 6 | Mutable global state | Stateful singletons, module-level mutable vars |
| 7 | Tight coupling to third-party | Direct dependency on vendor specifics without abstraction |
| 8 | Missing input validation | External data accepted without validation |
| 9 | Synchronous I/O | Blocking event loop with sync I/O calls |
| 10 | DB queries in loops | N+1 query pattern - batch or join instead |
| 11 | Missing transaction boundaries | Multi-step mutations without transactional guarantee |
| 12 | No rollback/cleanup on partial failure | Partial writes left dangling on error |
| 13 | TODO/FIXME in critical paths | Unresolved work markers in production-critical code |
| 14 | Inline pattern bypass | Inline constructs bypassing established top-of-file patterns |
| 15 | Mixed error handling | Multiple error strategies in same file |
| 16 | Inconsistent null handling | Mixed null/undefined treatment within same module |
| 17 | Heavy mock in sub-conftest | Mock for large deps (>50MB or native C/Fortran) in sub-directory conftest instead of root `tests/conftest.py` |
| 18 | Unmarked heavy-dep test | Test requiring real heavy dependency (scipy, ortools, ML models) without `slow`/`e2e` marker |
| 19 | Mock target on lazy import | `monkeypatch.setattr` path points to usage site, not definition site, for functions imported inside other functions |

---

## Mental Models

6 review perspectives - adopt relevant ones per review context.

| Perspective | Focus |
|---|---|
| **Security Engineer** | All input malicious, all dependencies compromised |
| **Performance Engineer** | Big-O analysis, I/O pattern assessment |
| **Team Lead** | 6-month maintainability, junior comprehension |
| **Systems Architect** | Failure modes, scalability, blast radius |
| **SRE** | 3 AM breakage risk, debugging difficulty |
| **Pattern Detective** | Dominant patterns per file, violation scanning |
| **Test Infrastructure Auditor** | conftest execution order, mock placement (root vs sub-conftest), external service mock coverage, test marker discipline, lazy import mock targeting, environment/platform compatibility |

---

## Severity Classification & Scoring

### Severity Levels

| Severity | Examples | Deduction |
|---|---|---|
| **CRITICAL** | Runtime crashes, data corruption, memory leaks, security vulns, silent wrong output on resume | -2 pts (security: -4 effective / 2x weight) |
| **HIGH** | Architectural violations, severe tech debt, boundary breaks, race conditions, accumulating resource leaks | -1 pt |
| **MEDIUM** | Design smells, tight coupling, testability issues, wasted work on resume, inaccurate progress | -0.5 pts |
| **LOW** | Minor inconsistency, naming, missed optimization, cosmetic state issues | Noted only |

### Scoring Rules

- Start at 10/10, floor at 1/10
- Score below 7 requires explicit justification with specific deductions listed
- Category scores: Security, Performance, Maintainability, Consistency, Overall

---

## Review Execution Protocol

7-step sequence - follow in order.

1. **Read code** - understand purpose and intent
2. **Assess context** - scope, maturity level, focus area
3. **Map system** - dependencies, data flow, integration points
4. **Critical scan** - find showstoppers immediately
5. **Targeted analysis** - work through relevant framework sections
6. **Synthesize findings** - organize by severity and impact
7. **Deliver review** - clear, actionable, specific recommendations

---

## Analysis Domains

7 domains - apply relevant ones based on code under review.

### 1. Security
- Input validation, sanitization
- Auth/authz checks
- OWASP Top 10 coverage
- Secrets management
- API security (rate limiting, CORS)
- Dependency vulnerability exposure

### 2. Performance
- Algorithm complexity (Big-O)
- N+1 queries, batching
- Caching strategy and invalidation
- I/O efficiency (async, streaming)
- Resource cleanup and pooling

### 3. Code Quality
- Readability and naming
- DRY - duplication detection
- Separation of concerns
- Error handling completeness
- Edge case coverage
- Function complexity (cyclomatic)

### 4. Architecture
- Design pattern correctness
- Business logic / IO separation
- Scalability considerations
- State management strategy
- Integration patterns (adapters, ports)

### 5. Testing & Observability
- Coverage level and quality
- Test isolation and determinism
- Logging (structured, leveled)
- Monitoring and alerting hooks

### 6. Pattern Consistency
- Error handling style uniformity
- Resource management conventions
- Import organization
- Null/undefined handling
- Async pattern consistency

### 7. Configuration & Infrastructure
- K8s manifests correctness
- IaC (Terraform, Pulumi) review
- CI/CD pipeline configuration
- Environment config separation (dev/staging/prod)
