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
