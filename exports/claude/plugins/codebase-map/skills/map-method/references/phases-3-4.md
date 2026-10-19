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

# Phases 3 and 4

## Phase 3: Flow Tracing

Trace critical execution paths through the codebase:

- Request lifecycle (entry → processing → response)
- Data transformation pipeline (input → validation → processing → output)
- Error propagation paths (where errors originate, how they're handled)
- State mutation flows (what changes state, side effects)
- Paths that gate entry into the product: authentication, onboarding, consent or policy acceptance, first-run setup. These are mandatory critical paths whenever this phase runs, not a `--critical` extra, because a user who cannot complete one reaches nothing else. For client code the trace covers what the screen actually renders, which means the effective style cascade over it (global selectors that reach the root or its first children, `position`, `overflow`, flex sizing, scroll locking) and not only the component logic. A global rule that overrides a screen's positioning is a defect on that path, and the trace ends at the control the user must reach. Run `cascade_scan.py` over the client root, never over a stylesheet directory alone, and cite, on the path, every rule it lists whose selector can match that screen.

If `--critical` flag is set, prioritize:
- Authentication/authorization flows
- Payment/transaction flows
- Data persistence flows

**Output file:** `$RUN_DIR/03-flows.md`

```markdown
# Phase 3: Flow Tracing

## Critical Paths
[Step-by-step flow descriptions with file:line references. Entry-gating paths first, each ending at the control the user must reach, with the stylesheet rules that govern that screen cited alongside the component]

## Data Flow
[How data transforms through the system]

## Error Handling Paths
[Where errors originate and how they propagate]

## Side Effects
[Functions with side effects and their blast radius]

## Process Diagrams

For each significant process discovered, generate a Mermaid flowchart diagram. Categorize each diagram as Technical, Functional, or End-to-End.

### Technical Processes
[Internal system mechanics - how components interact at code level]
[One Mermaid flowchart per process, e.g. request handling pipeline, database transaction flow, cache invalidation]

### Functional Processes
[Business logic flows - what the system does from a domain perspective]
[One Mermaid flowchart per process, e.g. user registration, order processing, notification dispatch]

### End-to-End Processes
[Full user journeys spanning multiple components and services]
[One Mermaid flowchart per process, e.g. complete purchase flow from cart to confirmation, onboarding flow from signup to first action]

Diagram guidelines:
- Limit to the 5 most critical/complex paths per category to avoid noise. Reference additional flows in prose.
- Use `flowchart TD` (top-down) for linear processes, `flowchart LR` (left-right) for pipelines
- Include decision nodes (`{condition}`) for branching logic
- Label edges with conditions, data passed, or HTTP methods
- Reference source files as comments: `%% src/auth/login.py::handle_request`
- Mark error/failure paths with dotted lines: `-->|error|`
- Keep each diagram under 30 nodes - split large processes into sub-diagrams

## Source reading
[Manifest, actual files/ranges, parser diagnostics and unresolved gaps]
```

---

## Phase 4: Semantic Understanding

This is the AI-powered phase -- understand the **WHY** behind the code:

- Business purpose of each module
- Design decisions and trade-offs (inferred from code patterns)
- Historical context (from git blame and commit messages)
- Assumptions embedded in the code
- Implicit contracts not documented anywhere
- Architecture Decision Records (ADRs) -- document rejected alternatives and WHY they were rejected, so future developers don't reintroduce failed approaches

**Output file:** `$RUN_DIR/04-semantics.md`

```markdown
# Phase 4: Semantic Understanding

## Module Purposes
[WHY each module exists, not just WHAT it does]

## Design Decisions
[Inferred decisions and their trade-offs]

## Architecture Decision Records
[For each significant design choice discovered, document as an ADR:]
- **Decision:** [What was chosen]
- **Context:** [What problem it solves]
- **Alternatives rejected:** [What was NOT chosen and WHY]
- **Consequences:** [Trade-offs accepted]

ADRs bridge the gap between temporal purity (document only the present) and historical
knowledge (don't repeat past mistakes). The code shows WHAT was chosen; ADRs preserve
WHY alternatives were rejected.

## Embedded Assumptions
[Assumptions the code makes that aren't documented]

## Hidden Contracts
[Implicit agreements between modules]

## Conventions to Follow
[Prescriptive rules derived from observed patterns]
- Error handling: [pattern]
- Logging: [pattern]
- Configuration: [pattern]

## Source reading
[Manifest, actual files/ranges, parser diagnostics and unresolved gaps]
```

## AI-Powered Semantic Analysis

### Five Layers of Understanding

| Layer | What | Who Does It |
|-------|------|-------------|
| **1. WHAT** | Classes, functions, imports | Scripts (AST) |
| **2. HOW** | Algorithm details, data flow | Semantic source reading |
| **3. WHY** | Business purpose, design decisions | Evidence-backed interpretation |
| **4. WHEN** | Triggers, lifecycle, concurrency | Behavioral tracing |
| **5. CONSEQUENCES** | Side effects, failure modes | Cross-module reasoning |

### Pattern Recognition

| Pattern Type | Examples | Documentation Focus |
|-------------|----------|---------------------|
| **Architectural** | Repository, Service, CQRS, Event-Driven | Responsibilities, boundaries |
| **Behavioral** | State Machine, Strategy, Observer, Chain | Transitions, variations |
| **Resilience** | Circuit Breaker, Retry, Bulkhead, Timeout | Thresholds, fallbacks |
| **Data** | DTO, Value Object, Aggregate | Invariants, relationships |
| **Concurrency** | Producer-Consumer, Worker Pool | Thread safety, backpressure |

### AI Analysis Workflow

```
1. STRUCTURE FIRST -> bound snapshot outline; classification and usages when needed
2. ANALYZE -> Read source, apply semantic questions, recognize patterns, identify red flags
3. DOCUMENT -> Use template, explain WHY not just WHAT, document contracts
4. VERIFY -> Re-trace the code path end to end; accept runtime evidence only when the user supplies it
```

## Analysis Loop Workflow

```
1. CLASSIFY -> LOC, dependencies, critical patterns, assign classification
2. READ & MAP -> AST structure, classes, functions, constants, state mutations
3. DEPENDENCY CHECK -> Internal imports, external imports, external calls
4. CONTEXT ANALYSIS -> Symbol usages, importing modules, message flows
5. CODE-PATH VERIFICATION (Critical/High-Complexity) -> Trace every call path the claim depends on; runtime logs or traces count only when the user supplies them, and are never invented
6. DOCUMENTATION -> Write the phase output file into the active run directory
```

## The Semantic Analysis Mandate

```
Scripts extract STRUCTURE:  "class Foo with method bar()"
Claude extracts MEANING:    "Foo implements Repository pattern for
                             caching user sessions with TTL expiration"

NEVER stop at structure. ALWAYS pursue understanding.
```

## Team mode

### Team extensions

| Heading | File | Mode | Writer | After | Aggregation |
|---|---|---|---|---|---|
| Cross-Partition Flows | 03-flows.md | consolidated | partition-synthesizer | Critical Paths | Merge (from <other>) / (to <other>) traces; deduplicate end-to-end flows, anchored at the earliest step. |
| Cross-Partition ADR | 04-semantics.md | consolidated | partition-synthesizer | Architecture Decision Records | Promote multi-partition ADRs to global rules, citing original locations. |
| Hidden Contracts (cross-partition) | 04-semantics.md | consolidated | partition-synthesizer | Hidden Contracts | Collect <this> ↔ <other> contracts in the canonical cross-partition registry. |

### Partition worker

For entry-gating paths, scan the whole run target, never the partition alone, and cite matching stylesheet rules wherever they live. Mark flows (from <other>) / (to <other>) and fence cross-partition diagrams with subgraphs. Include a cross-partition ADR only when this partition is one of its actors.
Annotate each cross-partition Hidden Contracts entry as `<this-partition> ↔ <other-partition>`.

### Consolidation

| File | Common heading | Rule |
|---|---|---|
| 03-flows.md | Critical Paths | Concatenate partition critical paths and cross-partition annotations. |
| 03-flows.md | Data Flow | Concatenate; add a nested summary of messages, shared tables and inter-partition HTTP calls. |
| 03-flows.md | Error Handling Paths | Concatenate and highlight cross-partition propagation. |
| 03-flows.md | Side Effects | Concatenate; separate cross-partition effects in a nested subsection. |
| 03-flows.md | Process Diagrams | Concatenate; add subgraph fences to cross-partition end-to-end diagrams. |
| 04-semantics.md | Module Purposes | Concatenate partition purposes. |
| 04-semantics.md | Design Decisions | Concatenate decisions. |
| 04-semantics.md | Architecture Decision Records | Concatenate partition ADRs. |
| 04-semantics.md | Embedded Assumptions | Concatenate; separate cross-partition assumptions in a nested subsection. |
| 04-semantics.md | Hidden Contracts | Retain partition-local contracts and mark shared ones <this> ↔ <other>. |
| 04-semantics.md | Conventions to Follow | Concatenate; expose incompatible conventions. |
