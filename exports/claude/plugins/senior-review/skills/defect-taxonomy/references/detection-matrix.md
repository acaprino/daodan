<daodan_host_binding host="claude">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Claude binding: repository tools are Read/Glob/Grep and Write/Edit; shell execution
uses Bash and network fetch uses WebFetch. Pass the executable string in Bash's
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

# Detection Strategy Matrix

Cross-cutting detection reference for all 16 defect taxonomy categories.

---

## Detection Matrix by Category

| # | Category | Static (AST/Lint) | Dynamic (Runtime/Fuzz) | Textual (Regex/Pattern) | Primary Tools | Priority |
|---|----------|-------------------|------------------------|-------------------------|---------------|----------|
| 1 | Concurrency & Parallelism | Thread Safety Analysis, RacerD, Infer | ThreadSanitizer, Go `-race`, Helgrind | Lock pattern grep, `synchronized` audit | TSan, Coverity, SpotBugs | Critical |
| 2 | Variable & State | `-Wuninitialized`, ESLint `react-hooks/exhaustive-deps`, NullAway | MSan, runtime null checks | `var` usage, mutable default grep | Clang-Tidy, ESLint, SpotBugs | High |
| 3 | Comparison & Logic | `-Wparentheses`, ESLint `eqeqeq`, SpotBugs `EC_*` | Mutation testing (PIT, Stryker) | Float `==` patterns, `is` vs `==` | ESLint, GCC warnings | Medium |
| 4 | Type & Conversion | TypeScript strict, `-Wconversion`, `-Xlint:unchecked` | UBSan, runtime type checks | Implicit cast patterns | TypeScript, UBSan, Clippy | High |
| 5 | Memory Management | Coverity, Clang Static Analyzer, Rust borrow checker | ASan, Valgrind, fuzzing | `malloc`/`free` balance, `new`/`delete` | ASan, Valgrind, Coverity | Critical |
| 6 | Security | CodeQL, Semgrep, Bandit, SpotBugs Security | DAST (ZAP, Burp), fuzzing | Taint patterns, secret regexes, dangerous APIs | CodeQL, Semgrep, TruffleHog | Critical |
| 7 | Error Handling & Resources | SpotBugs `OBL_*`, PMD, errcheck, Clippy | Resource leak detection, stress tests | Empty catch, bare except, missing defer | SpotBugs, errcheck, ESLint | High |
| 8 | API & Contract | NullAway, `-Xlint:overrides`, japicmp | Integration tests, contract tests | Override patterns, deprecated usage | Infer, Pact, japicmp | Medium |
| 9 | Distributed Systems | TLA+ model checking | Jepsen, Chaos Monkey, fault injection | Timeout config, retry config | Jepsen, Chaos Monkey | High |
| 10 | Communication & Protocol | Schema validators, proto lint | Connection pool monitoring, load tests | Missing timeout patterns | Pact, proto-lint | Medium |
| 11 | Integration & Components | ArchUnit, madge, import-linter | Integration tests, smoke tests | Circular import patterns, hardcoded URLs | ArchUnit, madge, Pact | Medium |
| 12 | Data & Persistence | ORM query analyzers, migration lint | `EXPLAIN ANALYZE`, slow query logs, load tests | N+1 patterns, missing index hints | bullet, nplusone, pg_stat | High |
| 13 | Performance & Resources | Complexity analyzers, allocation profilers | CPU/memory profiling, load tests, GC analysis | String concat in loop, unbounded collection | JFR, async-profiler, pprof | Medium |
| 14 | Design Pattern Misuse | SpotBugs, SonarQube pattern rules | Concurrency stress tests, leak detection | DCL patterns, singleton patterns | SonarQube, SpotBugs | Low-Medium |
| 15 | Build & Deployment | Dependency analyzers, config validators | Startup smoke tests, env parity checks | Secret patterns, hardcoded URL/IP | GitLeaks, Maven Enforcer | Medium |
| 16 | Testing & Observability | Mutation testing config, coverage tools, conftest structure analysis, mock target validation | Flaky test tracking, observability audits, platform hang detection | Missing log/metric patterns, heavy mock in sub-conftest, lazy import mock paths | PIT, Stryker, OpenTelemetry, ruff, pytest | High |

---

## Detection Priority Tiers

### Tier 1 - Critical (automate first)
- Category 1: Concurrency -- data races cause intermittent, hard-to-reproduce bugs
- Category 5: Memory -- buffer overflows and use-after-free are exploitable
- Category 6: Security -- injection and auth flaws are directly exploitable

### Tier 2 - High (automate next)
- Category 2: Variable/state -- null refs are most common crash cause
- Category 4: Type/conversion -- overflow/truncation cause silent data corruption
- Category 7: Error handling -- resource leaks cause production outages
- Category 9: Distributed -- split-brain and retry storms cause cascading failures
- Category 12: Data -- N+1 and missing indexes cause performance degradation at scale
- Category 16: Testing infrastructure -- conftest ordering, mock placement, and platform hangs cause blocking test failures

### Tier 3 - Medium (targeted checks)
- Categories 3, 8, 10, 11, 13, 15: Important but lower blast radius or easier to catch in review

### Tier 4 - Low-Medium (periodic audits)
- Category 14: Design pattern misuse -- catch in architecture reviews

---

## Highest-ROI Detection Investments for AI Agent

1. **Taint analysis for security** (category 6 + injection subtypes)
   - Track user input flow to dangerous sinks (SQL, shell, HTML, file ops)
   - Covers: SQLi, XSS, command injection, path traversal, SSRF
   - Implementation: data flow graph from HTTP input to sink functions

2. **Null/type-flow analysis for correctness** (categories 2, 3, 4, 8)
   - Track nullable values through call chains
   - Detect implicit coercions, unchecked downcasts, missing null guards
   - Implementation: type state tracking per variable through control flow

3. **Resource lifecycle tracking for reliability** (categories 5, 7, 10)
   - Match open/close, acquire/release, lock/unlock pairs
   - Detect leaks on exception paths, missing finally/defer
   - Implementation: resource state machine -- opened -> used -> closed, flag non-closed paths

4. **Concurrency analysis for safety-critical** (category 1)
   - Identify shared mutable state accessed without synchronization
   - Detect lock ordering inconsistencies
   - Implementation: access-lock pairing analysis, happens-before graph

---

## Language-Weighted Focus

| Language Family | Primary Risk Categories | Key Defect Types |
|----------------|------------------------|------------------|
| **C/C++** | 1 (Concurrency), 5 (Memory) | Data races, buffer overflow, use-after-free, dangling pointers, memory leaks |
| **JVM (Java/Kotlin/Scala)** | 2 (State), 7 (Error handling), 8 (API contracts) | Null refs, resource leaks, unchecked exceptions, API misuse, type erasure |
| **JS/TS** | 4 (Types), 6 (Security) | Type coercion, XSS, prototype pollution, async anti-patterns, stale closures |
| **Python** | 4 (Types), 6 (Security), 16 (Testing) | Type errors at runtime, injection, mutable defaults, GIL misconceptions, conftest ordering, mock target errors, heavy dep mock placement |
| **Go** | 1 (Concurrency), 7 (Error handling) | Goroutine leaks, unchecked errors, variable shadowing with `:=`, channel deadlocks |
| **Rust** | 1 (Concurrency), 8 (API contracts) | Unsafe blocks, logic errors (compiler catches memory/type), unwrap in prod |

---

## Underrepresented in Standards (Custom Heuristics Needed)

These categories lack CWE identifiers but cause major production incidents:

| Category | Defect Types | Why No CWE | Heuristic Approach |
|----------|-------------|-----------|-------------------|
| **9 - Distributed Systems** | Split-brain, saga compensation, retry storms, consensus bugs | CWE focuses on single-process software | Pattern-match on distributed primitives: retry config, timeout presence, idempotency key usage, circuit breaker config |
| **10 - Communication** | Protocol drift, missing heartbeat, timeout misconfiguration | Protocol-level issues outside CWE scope | Grep for HTTP/gRPC client creation without timeout, missing DLQ config, heartbeat interval settings |
| **11 - Integration** | Circular dependencies, config drift, feature flag interactions | Architectural issues, not code-level | Dependency graph analysis, config source audit, flag inventory age tracking |
| **13 - Performance** | Algorithmic complexity, unbounded growth, GC thrashing | Performance not traditionally security/safety | Loop nesting analysis, collection growth without bounds, allocation hotspot detection |
| **16 - Testing Infrastructure** | Conftest scope errors, collection-order mock failures, platform initialization hangs, monkeypatch target errors, incomplete service mocking | CWE focuses on production code, not test infrastructure | conftest hierarchy analysis (root vs subdirectory placement of `sys.modules` mocks), import graph tracing for mock target validation, external service client inventory vs mock inventory diff, platform-specific plugin interference checklist |

---

## Quick Detection Checklist (Per Review)

- [ ] Taint: User input reaches SQL/shell/HTML/file sink?
- [ ] Null: Nullable value dereferenced without check?
- [ ] Resource: Every open/acquire has matching close/release on all paths?
- [ ] Concurrency: Shared mutable state accessed from multiple threads?
- [ ] Type: Implicit conversions or unchecked casts present?
- [ ] Error: Catch blocks empty or overly broad?
- [ ] Timeout: All I/O operations have explicit timeouts?
- [ ] Idempotency: Retryable operations are idempotent?
- [ ] Index: Queries on large tables use indexed columns?
- [ ] Secret: No hardcoded credentials or keys?
- [ ] Test mocks: Heavy deps mocked in root conftest, not sub-conftest?
- [ ] Mock targets: monkeypatch/patch paths resolve to actual module-level attributes?
- [ ] Test markers: Tests needing real heavy deps have `slow`/`e2e` marker?
- [ ] External mocks: All external services mocked in integration conftest?
