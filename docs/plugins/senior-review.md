# Senior Review Plugin

> Catch bugs before they ship. Twelve specialized agents: eleven review code quality, security, UI timing, distributed flows, startup cycles, temporal resilience (failure-over-time), data integrity (persistence semantics), resource lifecycle (ownership and release), cross-component logic integrity, formal API contracts, and codebase hygiene in parallel, and the twelfth, `premise-auditor`, derives the code's claims a second time, independently, and attacks the premises findings stand on. The reviewers read a shared contract/invariant map built by `codebase-map:semantic-interconnect-mapper`, which is why they find bugs that are invisible from local-only inspection. Backed by a comprehensive defect taxonomy knowledge base with 140+ defect patterns and CWE/OWASP mappings. `/daodan:review-branch` runs all of it as a single pipeline, with an adversarial verification panel and a completeness critic as quality gates before the report ships.

Command examples and named tools in this guide use Claude notation. For other
hosts, use the entry points and bindings in the source-derived reference below
and [host setup](../hosts.md).

React, TypeScript and platform providers are mandatory installation dependencies.
The relevant target signals select execution; false signals carry code-based skip
reasons, and unavailable matched workers remain failed deliveries. Explicit team
reviewer scope is respected. --no-context and --fast keep applicable stack
dimensions while changing context and verification behavior. Lifecycle candidate
reviews use this same engine. The generated dependency reference below records
the larger installation closure, including costs inherited by consumers.

Explicit team selectors include react, typescript and platform. Existing react-perf
and ts-safety selectors remain accepted; performance selects React performance for
a verified React target and general performance otherwise. Each request resolves
once before dispatch and is shown in the review plan.

Specialist reports keep their native labels and evidence. The same evidenced-finding
contract adds the confidence, premise and normalized severity required by the
review gates. Incomplete fields receive one completion request; an unresolved
delivery stays failed and its raw findings remain visibly unverified. A priority
label alone cannot establish confidence or measured performance impact.

A candidate supplied by project-lifecycle takes precedence over Git auto-detection.
Its scope, baseline and current snapshot include scoped untracked content. A clean
candidate does not fall back to the previous commit; missing baseline evidence
remains a declared comparison gap.

## Agents

### `code-auditor`

Adversarial code quality auditor combining architecture review, failure flow tracing, pattern consistency analysis, and quantitative scoring.

| | |
|---|---|
| **Model** | `inherit` |
| **Use for** | Architecture integrity, failure path analysis, pattern consistency, quality scoring |

**Invocation:**
```
Use the code-auditor agent to review [system/codebase]
```

**Methodology:**
- 4 cognitive frameworks (Boundary Detective, Abstraction Inspector, Chaos Engineer, State Auditor)
- 6-phase failure flow analysis (persisted state, kill points, resume/retry, cache invalidation, resource lifecycle, async concurrency)
- 16-item anti-pattern checklist
- 6 mental models (security engineer, performance engineer, team lead, systems architect, SRE, pattern detective)
- Quantitative 1-10 Code Quality Score per category (Security, Performance, Maintainability, Consistency, Resilience)
- References `defect-taxonomy` skill for CWE-mapped detection strategies

---

### `security-auditor`

Security auditor with attacker mindset specializing in vulnerability detection, CWE/OWASP mapping, and attack scenario construction.

| | |
|---|---|
| **Model** | `inherit` |
| **Use for** | Security audits, vulnerability assessment, OWASP/CWE compliance, threat modeling |

**Invocation:**
```
Use the security-auditor agent to audit [system/codebase]
```

**Expertise:**
- Input trust boundaries (injection, XSS, path traversal, command injection)
- Auth/authz (JWT, CSRF, privilege escalation)
- Secrets and cryptographic misuse
- API and header security
- Dependency vulnerabilities
- References `defect-taxonomy` skill for comprehensive CWE-mapped patterns

---

### `ui-race-auditor`

Framework-agnostic UI race condition analyst detecting timing bugs between async data loading, rendering, and event handlers.

| | |
|---|---|
| **Model** | `inherit` |
| **Use for** | UI timing bugs, scroll races, focus races, stale closures, measurement races |

**Invocation:**
```
Use the ui-race-auditor agent to analyze [UI component/codebase]
```

---

### `distributed-flow-auditor`

Adversarial cross-service flow analyst for microservices, agent-based, and multi-module distributed systems. Traces request flows, API/message contracts, saga orchestration, timeout chains, and integration boundaries across multiple services or modules.

| | |
|---|---|
| **Model** | `inherit` |
| **Use for** | Cross-service analysis, distributed flow tracing, contract verification, multi-service code review |

**Invocation:**
```
Use the distributed-flow-auditor agent to analyze [multi-service system]
```

**Methodology:**
- 6-phase analysis: service topology discovery, contract extraction, cross-boundary flow tracing, timeout chain validation, resilience pattern audit, message ordering and delivery
- Hunts for contract mismatches, cascading timeout violations, missing idempotency, broken saga compensation, message ordering bugs, and split-brain risks
- Both sides of every boundary verified: producer `file:line` AND consumer `file:line`
- References `defect-taxonomy` skill for CWE-mapped detection strategies

---

### `chicken-egg-detector`

Detects chicken-and-egg problems, circular initialization dependencies, and bootstrap deadlocks across services, modules, and infrastructure. Traces startup ordering, init sequences, config bootstrapping, and migration dependencies.

| | |
|---|---|
| **Model** | `inherit` |
| **Use for** | Startup dependency analysis, circular initialization detection, bootstrap cycle auditing, service startup ordering review |

**Invocation:**
```
Use the chicken-egg-detector agent to analyze [system/infrastructure]
```

**Methodology:**
- 6-phase analysis: component inventory and init sequence discovery, dependency graph construction, bootstrap sequence analysis, temporal coupling detection, migration and schema dependency analysis, infrastructure dependency mapping
- Finds cases where component A requires B to be ready but B requires A, creating deadlocks, flaky startups, or hidden temporal coupling
- Concrete evidence: every finding includes file:line references for both sides of the dependency cycle
- References `defect-taxonomy` skill for integration error patterns

---

### `temporal-resilience-auditor`

Adversarial reviewer for failure-over-time behavior in long-running code. Hunts the bugs that only exist on the time axis: retry loops without backoff or cap, errors swallowed until a subsystem silently dies, in-flight guards never cleared, timers that stop re-arming, missing escalation paths, and clock hazards (suspend, DST, throttled timers). Its core question is not "does this code work" but "what does the user see after this has been failing for a day".

| | |
|---|---|
| **Model** | `inherit` |
| **Use for** | Timers, schedulers, polling loops, retry/reconnect logic, queue workers, updaters, watchdogs, any process expected to stay alive for hours |

**Invocation:**
```
Use the temporal-resilience-auditor agent to analyze [long-running subsystem]
```

**Methodology:**
- 5-phase analysis: temporal machinery inventory, three-horizon failure-repetition analysis (1st failure, Nth failure, never-ending failure), silent-death detection, user-visible consequence tracing, clock and environment hazards
- Every quantitative claim labeled `measured` or `derived`; a derived number alone cannot justify Critical severity
- "None (silent)" as user-visible consequence is a severity escalator, never a mitigation
- Activated in the branch review (`/daodan:review-branch`) and the code-review variant (Agent L) by long-running/scheduled-execution signals in the diff
- References `defect-taxonomy` skill for concurrency and integration patterns

---

### `data-integrity-auditor`

Adversarial reviewer for persistence semantics. Central question: can the system produce, store, or read an impossible or inconsistent state? Hunts application-only invariants (uniqueness assumed in code, not constrained in the schema), lost updates, check-then-act races, partial writes, cache/database divergence, unstable pagination, and eventual consistency consumed as strong.

| | |
|---|---|
| **Model** | `inherit` |
| **Use for** | Schemas, models, ORM entities, repositories, raw SQL, cache layers, transaction boundaries |

**Invocation:**
```
Use the data-integrity-auditor agent to analyze [persistence layer]
```

**Methodology:**
- 5-phase analysis: write-path inventory, invariant enforcement gap analysis (code / schema / both / neither), concurrency anomaly hunt, multi-store divergence, representation hazards (soft delete, time, money, NULL, pagination)
- Distinct from logic-integrity by design: a domain rule violated in application logic is theirs; a store that can be made to hold an impossible state is this agent's territory
- Activated by persistence signals in the branch review (`/daodan:review-branch`) and as Agent M of the code-review variant
- References `defect-taxonomy` skill (`data-design-ops.md`, `concurrency-state.md`)

---

### `resource-lifecycle-auditor`

Adversarial reviewer for resource ownership and release. Central question: does every acquired resource (file, socket, connection, subprocess, listener, lock, task, timer) have a single owner and a guaranteed release path on success, on error, AND on cancellation? Hunts leaks, double-release, use-after-release, unbounded pool growth, and listeners that outlive their subject.

| | |
|---|---|
| **Model** | `inherit` |
| **Use for** | Code acquiring or managing resources, especially C/C++/Rust/Go and async-heavy systems where cancellation paths multiply |

**Invocation:**
```
Use the resource-lifecycle-auditor agent to analyze [resource-managing code]
```

**Methodology:**
- 4-phase analysis: acquisition inventory, release-path verification across the three exits, pool and registry discipline, lifetime mismatch hunt
- Prefers structural fixes (RAII, `with`/`defer`/`finally`, AbortController, effect cleanup) over manually paired calls
- Conditional, never always-on; activated by acquisition signals in the branch review (`/daodan:review-branch`) and as Agent N of the code-review variant
- References `defect-taxonomy` skill (`memory-resources.md`, `concurrency-state.md`)

---

### `logic-integrity-auditor`

Adversarial reviewer that hunts for violations of contracts, invariants, assumptions, domain rules, ordering, idempotency, and state machines documented in the interconnect map. Catches bugs no local-only reviewer can see: logic drift across components, implicit contracts silently broken, terminal states mutated, retry paths double-committing.

| | |
|---|---|
| **Model** | `inherit` |
| **Use for** | Branch review (`/daodan:review-branch`) Phase 2 (always-on in the review preset); logic/contract/invariant audit of code with an associated interconnect map |

**Invocation:**
```
Used automatically by the branch review (/daodan:review-branch); requires .team-review/02-interconnect.md (produced by semantic-interconnect-mapper)
```

**Methodology:** Reads the interconnect map + target files, proves violations of documented contracts / invariants / domain rules / assumptions. Stops and reports if interconnect map is absent (precondition failure).

---

### `premise-auditor`

Second, independent derivation of the code's claims, and attack on the load-bearing assumptions behind findings built from a common artifact. It exists because a pipeline that derives one premise and then explores it with N agents has one observer, not N.

| | |
|---|---|
| **Model** | `inherit` |
| **Tools** | Read, Write, Glob, Grep, Bash |
| **Use for** | Branch review (`/daodan:review-branch`) Phase 1c (independent derivation) and Lens 0 of the adversarial verification panel (premise challenge). It does not hunt defects |

**Invocation:**
```
Used automatically by the branch review (/daodan:review-branch); the spawning prompt names the mode
```

**Methodology:**
- Two modes with different inputs, never blended
- **Mode 1, independent derivation (Phase 1c):** blind to `.codebase-map/` in any form and to `.team-review/02-interconnect.md`; if its prompt paraphrases a Codebase Map conclusion it reports the contamination instead of proceeding. It establishes what is true about the concepts the diff touches by reading callers, callees, tests and the documents the knowledge leads point at, hunts for multiplicity (a second path where the code appears to have one), and writes `.team-review/01b-independent-claims.md`. It derives only: no comparison, no review, no fixes, no severity
- **Mode 2, premise challenge (Lens 0):** full context. It tries to falsify the proposition a finding stands on, across every path that proposition ranges over, rather than the finding itself, and returns `HOLDS`, `REFUTED` or `UNCERTAIN`
- `REFUTED` requires a `file:line` counterexample and names whether it kills the PREMISE or only a piece of shared SUPPORT; without a counterexample the verdict is `UNCERTAIN`
- A premise that paraphrases the finding instead of stating one falsifiable proposition is reported `premise_form: non-compliant`; the auditor derives the real premise and challenges that
- Not spawned under `--no-context`

---

### `api-contract-auditor`

Adversarial auditor for formal API contracts: OpenAPI / Swagger, JSON Schema, GraphQL SDL, gRPC `.proto`, AsyncAPI for event schemas, TypeScript DTOs, Pydantic models. Hunts for contract-code drift, breaking changes hidden as minor version bumps, missing nullable markers, type mismatches between producer and consumer schemas, underspecified error responses.

| | |
|---|---|
| **Model** | `inherit` |
| **Tools** | Read, Glob, Grep, Bash |
| **Use for** | Auditing OpenAPI/Swagger/GraphQL/gRPC specs for drift vs implementation; reviewing a PR that touches an API boundary; spec-first development audit; checking backwards compatibility before a release |

**Invocation:**
```
Use the api-contract-auditor agent to review [spec file or API boundary]
```

**Methodology:**
- 5-phase audit: contract inventory (find every spec artifact) -> contract-vs-implementation drift -> breaking-change detection (BREAKING / SAFE / AMBIGUOUS classification) -> consumer-side audit (hand-written + generated clients) -> cross-contract coherence
- Every finding cites producer `file:line` AND consumer `file:line`
- Handles OpenAPI 3.1, GraphQL SDL, gRPC, AsyncAPI, JSON Schema, Pydantic, TypeScript DTOs, Zod schemas
- Fulfills the `semantic-interconnect-mapper` `## Contracts` (formal) anchor

---

### `cleanup-auditor`

Adversarial codebase hygiene auditor. Detects dead code, orphan assets, phantom/unused dependencies, barrel-file bloat, eager-bundling anti-patterns, rebrand residue, stale documentation and historical artifacts, and lifecycle residue (leftovers of completed migrations and refactors, temporary debug tooling) inferred via commit-history and session-transcript archaeology. Every one of its dimensions needs source comprehension; what the filesystem and git decide alone (generated artifacts tracked in VCS, filesystem garbage, `.gitignore`, scratch directories, orphan doc-assets, stale stashes, worktrees and branches) belongs to `repo-hygiene:workspace-auditor`. Report-only; the fix is delegated to `senior-review:application-cleanup-method` with commit authorization (`/daodan:tidy-repo`, or Step 7c of the code-review variant).

| | |
|---|---|
| **Model** | `inherit` |
| **Tools** | Read, Write, Glob, Grep, Bash |
| **Use for** | Codebase cleanup review, technical-debt audit, dead-code detection with asset and dependency coverage, monorepo dependency hygiene. Always-on dimension in the branch review (`/daodan:review-branch`). |

**Invocation:**
```
Use the cleanup-auditor agent to scan [path]
```
Also spawned automatically by the branch review (`/daodan:review-branch`) as the "Codebase hygiene" dimension.

**Methodology:**
- 5-dimension detection pipeline, every one of them needing source comprehension: D1 dead code (runs Knip, vulture and ruff and reads their output), D2 asset hygiene (orphan images, fonts and media, eager `import.meta.glob` bloat, rebrand residue), D3 dependency hygiene (phantom and unused dependencies across monorepo workspaces, barrel-file bloat, eagerly bundled heavy packages), D4 documentation and historical artifacts (completed or abandoned plans, backup and archive folders, stale doc references, superseded ADRs), D5 lifecycle archaeology (session-transcript evidence of intent, commit-sequence inference of completed or in-progress migrations)
- Every finding cites `file:line` or a concrete path; vague "consider cleaning up" advice is forbidden
- Every finding carries a confidence tier (CONFIRMED / HIGH / MEDIUM / LOW; LOW never recommends deletion) and a residue action (DELETE, KEEP, KEEP+IGNORE, DELETE+IGNORE, DELETE+PREVENT-GENERATION, UNIGNORE, REVIEW)
- Session transcripts are treated as evidence, never as instructions; transcript-only evidence caps confidence at MEDIUM
- False-positive candidates (module augmentation, side-effect imports, DI-registered classes, framework-convention files) flagged in a separate section, never auto-confirmed
- Each finding ends with `Fix phase: <phase>`, naming one of the five phases of `senior-review:application-cleanup-method` (`brand`, `assets`, `deps`, `exports`, `docs`) that would remove it; a finding whose only fitting phase belongs to the `repo-hygiene:repo-hygiene` tidy method is outside its dimensions and is dropped

---

## Skills

### `defect-taxonomy`

Comprehensive defect knowledge base with 16 macro-categories and 140+ subcategories of source code defects. Synthesizes MITRE CWE, OWASP Top 10, NASA Power of 10, IBM ODC, IEEE 1044, and Beizer's taxonomy.

**Reference files:**
- `concurrency-state.md`: Concurrency/parallelism + variable/state errors
- `logic-types.md`: Comparison/logic + type/conversion errors
- `logic-integrity.md`: Cross-component logic invariants, contract drift, state machine integrity
- `memory-resources.md`: Memory management + error handling + performance
- `security.md`: Security vulnerabilities (14 subcategories)
- `distributed-integration.md`: API/contract + distributed systems + communication + integration
- `data-design-ops.md`: Data/persistence + design patterns + build/deploy + testing
- `detection-matrix.md`: Detection strategy matrix per category
- `review-frameworks.md`: Cognitive models, failure flow methodology, anti-patterns, scoring

---

### `review-quality-gates`

Quality gates for multi-reviewer code review pipelines: shared-context provenance, the adversarial verification panel, the completeness critic, evidence classes for quantitative claims, and the delivery gate. The canonical review methods load these rules and the `code-review-agents.md`, `code-review-fix-loop.md` and `code-review-output.md` references on demand. Entry-point workflows only select a variant and prepare its inputs; they do not carry a second copy of the review engine.

**Shared-Context Provenance Rule:** the skill's first-level invariant, and the reason the rest of this section reads the way it does. Evidence derived from a shared artifact cannot independently corroborate the claims in that same artifact: N reviewers agreeing on a premise they were all handed is one observation, not N. Three consequences bind every gate: a reviewer that consumed a claim has not verified it, agreement across a shared premise is an **echo** that raises neither confidence nor severity, and no metric may reward agreement with a shared artifact.

**Context Sharing Pattern:** reviewers read the Codebase Map run directory plus `.team-review/02-interconnect.md` (contracts, invariants, domain rules, assumptions, integration hot-spots) and `.team-review/01-knowledge-provenance.md`, guided by anchor routing per dimension (security reads Integration Hot-Spots plus unverified Assumptions; logic-integrity reads Contracts, Invariants, and Domain Rules; and so on). Every finding declares two extra fields: its **load-bearing premise** (the single proposition whose falsity collapses it) and that premise's **provenance** (`independent`, `shared-context`, or `mixed`, recording causal dependence rather than citation). The **map utilization rate** (share of findings citing a map anchor) is an operational number only, and no target is set for it: a high value on a wrong map is the signature of the failure this pipeline exists to prevent. The quality signals are elsewhere: independent premise reconstruction rate, premise challenge rate, map challenge rate, map gap rate, and cross-source corroboration.

**Reviewer catalog and scoped context:** reviewer selection reads the compiled `reviewer-catalog.json` in review-preparation's references: identities, triggers, prerequisites, body digests and host bindings generated from the role kernels, so preparation never scans role kernels at runtime. With no interconnect map, a scoped semantic context (Code Graph rows from `symbols-at`, `edit-impact` or `stale-callers`, plus records, documents and cards, each with provenance and freshness) can serve `logic-integrity-auditor`; premise-auditor Mode 1 remains blind to shared context, while Lens 0 in Mode 2 receives the full admitted context.

**Adversarial Verification Panel:** every finding above a 50% confidence floor is judged by up to 4 lenses (Premise Challenge, Reachability/Correctness, False-Positive Causes, Severity Calibration). **Lens 0 is a veto, gated and first.** It runs on findings whose premise provenance is `shared-context` or `mixed`, and on any finding whose declared premise carries a universal or negative quantifier (`no`, `never`, `cannot`, `always`, `only`) at any provenance, since an over-scoped premise can be born independently as easily as it can be inherited. It attacks the premise rather than the finding and returns `REFUTED` only with a `file:line` counterexample, stating whether that counterexample kills the PREMISE itself or only a piece of shared SUPPORT: killing the premise discards the finding as `filtered: premise-refuted` without spending lenses 1-2, while `UNCERTAIN` proceeds tagged `premise-contested`. It never kills a finding by failing, since error, malformed output and evidence-free refutation all collapse to `UNCERTAIN`. Lenses 1-2 then run in parallel; lens 3 is **gated on survival** (calibrating a finding about to be discarded is spend for nothing, and the gate cuts roughly a third of verifier calls). A finding survives if at least 2 of lenses 1-2 vote REAL, is discarded (`filtered`) if at least 2 vote FALSE_POSITIVE, and survives `contested` on a tie. Final severity comes from lens 3's vote. A cost guard (a finding-count proxy, not a token budget) narrows verification to Critical/High plus an uncertainty band once more than 25 findings survive dedup, unless `--rigorous` is passed; `--fast` skips the panel entirely.

**Evidence Classes:** any finding that quantifies damage labels the number `measured` (harness, simulation, logs, with the method stated) or `derived` (computed by reading the code). A `derived` number alone cannot justify Critical severity, and no finding can be closed as acceptable ("bounded", "low traffic") without also answering the **user-visible-consequence question**: what does the user see, and when? "Nothing, silently" escalates severity rather than closing the finding.

**Delivery Gate:** every spawned reviewer is accounted for by a findings file, an explicit no-findings report or a failed delivery. A silent reviewer is nudged once; collected partial output remains marked undelivered and the dimension is **degraded**, never presented as clean. Workspace cleanup uses the run's owned-file manifest and hashes, preserving preexisting files, foreign edits, unresolved evidence and resume data. An unchanged owned probe can be removed only after its conditions, commands, outcomes and limitations are retained in the report and its evidence references still resolve. Persistent run retention belongs to the caller's consolidate path.

**Completeness Critic:** one agent checks coverage against a fixed gap taxonomy (dimensions warranted but not run, in-scope files cited by no finding, unverified interconnect assumptions untouched by any finding, high-risk hot-spots with zero findings, and findings closed on a metric alone without a stated user-visible consequence) and may trigger one bounded follow-up round for the single highest-risk gap it names.

**Reviewer Pipeline Conventions:** every Phase 2 reviewer carries a scope budget (stops after ~15 file reads without a finding), a no-findings protocol (a clean "examined X, Y, Z: no issues" report is valid, not a failure), and a `## Cross-Reviewer Notes` section for observations that belong to another dimension.

---

### Reusable review methods

`review-preparation` resolves the variant's scope, flags, exact snapshot and shared context. `review-method` owns the code-review, team-review and pr-review procedures. `review-consolidation` accounts for core and extension deliveries, applies the same provenance and verification rules, and writes the native report with a `project-result` envelope. The seven review-domain schemas retain their own finding and evidence meanings; [project-protocol](project-protocol.md) owns operational state and candidate validation.

`application-cleanup-method` exposes the former Step 7c subtraction procedure to reviews and lifecycle plans. Its inputs include accepted findings and severities, completed targeted fixes where needed, a clean exclusively owned isolated worktree, meaningful build/test gates and commit authorization. It does not add another auditor.

## Entry points and variants

The plugin has no command of its own. `/daodan:review-branch` runs `senior-review:review-method` with shape `branch`: the team-review variant on a branch against its base, the pr-review variant on a pull request. `/daodan:review-changes` runs shape `light` (`references/light.md`) on the current changes, a commit, a file or a document. The code-review variant remains inside the method for callers that name it.

### Branch review: the team-review variant (`/daodan:review-branch`)

Multi-dimensional code review as a **6-phase pipeline**: independent evidence discovery and context building first, so reviewers hunt cross-component logic bugs, not just what's visible from local inspection.

**Execution:** dispatch, isolation and result collection come from the host harness, so nothing beyond `senior-review`'s own dependencies is needed. Every reviewer runs in its own context, exactly the selected dimensions are dispatched once each, and every reviewer is recorded delivered or failed before anything is consolidated. If the host cannot run reviewers in isolated contexts, the command stops and says so.

| | |
|---|---|
| **Options** | `<target> [--reviewers auto\|security,performance,...] [--base-branch main] [--all] [--deep] [--no-context] [--fast] [--rigorous]` |
| **Artifact dir** | `.team-review/` (state, scope, interconnect map, per-dimension findings, consolidated report; preserved, not auto-deleted) |

**Pipeline:**

| Phase | What happens |
|-------|---------------|
| 0. Target resolution | Resolves `<target>` (path, git diff range, or PR number) and collects the diff |
| 0b. Context detection | Auto-selects review dimensions from changed files and codebase signals (skipped if `--reviewers` is explicit) |
| 0c. Review evidence discovery | Inline. Discovers what evidence this review needs from the project's own indexes and tests, forbidden from reading `.codebase-map/` in any form including prior runs, and writes the immutable `.team-review/01a-review-knowledge-leads.md` |
| 1a. Codebase Map analysis | Runs the analyze entry of `codebase-map:map-method` in the orchestrating context, not as a dispatched worker (`--depth=lite` by default, full with `--deep`); halts the pipeline if it produces no output |
| 1c. Independent premise derivation | `premise-auditor` in mode 1, spawned in the same turn as 1a and blind to its output, writes `.team-review/01b-independent-claims.md`. A second observer, not the same observer consulted twice |
| 1d. Knowledge reconciliation | Inline join of 01a, 01b and Codebase Map's `knowledge/documentation-leads.md` into `.team-review/01-knowledge-provenance.md`, keeping `Missing` and `Disputed` strictly apart |
| 1b. Interconnect mapping | `semantic-interconnect-mapper` builds `.team-review/02-interconnect.md`, turning every contradiction between the two derivations into a `disputed` row |
| 2. Adversarial review | Spawns one reviewer per dimension in parallel, each reading the Codebase Map run directory, the interconnect map and the knowledge provenance, and declaring the load-bearing premise and provenance of every finding |
| 3. Monitor and collect | Delivery gate: consolidation does not start until every spawned reviewer has delivered its findings file or an explicit no-findings report; a silent reviewer is nudged once, then salvaged and reported as degraded |
| 4. Consolidation | Deduplicates findings, resolves severity conflicts, weighs agreement by premise provenance (independent agreement corroborates, shared-premise agreement is an echo), collects `[MAP-GAP]` findings as mapper coverage gaps, organizes by severity; writes `.team-review/99-consolidated.md` |
| 4b. Adversarial verification | Quality gate, see `review-quality-gates` above (skipped with `--fast`) |
| 4c. Completeness critic | Quality gate, see `review-quality-gates` above (skipped with `--fast`) |
| 5. Report & cleanup | Compare the complete workspace baseline and owned-artifact manifest; preserve conclusions before removing unchanged owned probes. Report map utilization, premise metrics, corroboration and echoes; preserve `.team-review/` for later reference |

**Always-on dimensions:** security, architecture, logic integrity (skipped under `--no-context`), codebase hygiene (`cleanup-auditor`), workspace hygiene (`repo-hygiene:workspace-auditor`: filesystem garbage, generated artifacts tracked in VCS, `.gitignore` completeness, scratch and pipeline-output directories, orphan doc-assets, git auxiliary state; disjoint from codebase hygiene by construction).

**Conditional dimensions** use change signals to select UI races, distributed flows, circular dependencies, temporal resilience, data integrity, resource lifecycle and API contracts. Structural entropy dispatches `abstraction-architect:abstraction-architect-agent`; test quality dispatches `testing:test-suite-auditor`. These are declared required providers. General performance uses code-auditor; data migrations use data-integrity-auditor. Logic findings about rules absent from the interconnect map retain `[MAP-GAP]` and mapper coverage limitations. React performance, TypeScript type safety and platform integration are selected from the relevant package and target signals by the same preparation method. Their canonical roles remain in [react-development](react-development.md), [typescript-development](typescript-development.md) and [platform-engineering](platform-engineering.md); one selection, delivery ledger, verification panel and report account for them alongside every other dimension. Missing required workers remain failed deliveries; generic verifier or critic tasks use an explicitly declared isolated worker, never substitute for a missing specialist.

The variant's targets are a path, a git diff range or a PR number. `/daodan:review-branch` passes a branch against its base, or the current branch; a pull request runs the pr-review variant below. Its options select explicit dimensions (`--reviewers security,testing`), verify every finding (`--rigorous`) or run raw mode with no context phase (`--no-context`).

`--no-context` reproduces the pre-pipeline behavior: no context phase, reviewers see only the target and diff, and `logic-integrity-auditor` reports its missing prerequisite instead of running. Use it for quick scans or targets under roughly 100 LOC.

---

#### The roster is computed, not chosen

Since 15.4.0 the reviewer never decides its own rigor. The first live run of the
task cycle (2026-10-19) dispatched seven reviewers, a security auditor and a
Git-history pass among them, for a fix inside one function, because the method
said "proportionate to risk" and the model did everything. Now
`review_roster.py` in `project-protocol` reads the diff and the map's impact
packet and writes the roster into the run: shape `light` (tools, then one
generalist, before a commit) or `branch` (tier `small`, `medium` or `large`
before a merge). A changed public interface, a sensitive path, a changed
manifest or many callers force `large`; `--deeper` is the caller's one step up;
nothing lowers a tier. The protocol refuses a delivery whose role is outside
the roster. The same probe diff computes `small`: three reviewers instead of
seven.

Since 15.5.0 the roster also depends on what is reviewed. A light review has one
reviewer: the code auditor for a changeset, the premise auditor's claim check
(its Mode 3) for a decision record, a plan or a document. A branch review of a
plan, a specification or a document gets its kind's fixed set. Every review of a
task appends its own entry to the run's `reviews` list, which is append-only, and
each delivery names the review it belongs to: one roster can no longer refuse a
wave's writer or the reviewers of another stage. The light review is one unit,
`review-method/references/light.md`, read alone: the variant references belong
to the branch review, and before this release the light shape ran the
code-review variant, which always dispatched security, hygiene and history
reviewers whatever the roster said.

#### Investigation, the review run in reverse

`investigation-method` starts from an observed error and looks for its cause
without fixing it. It collects the facts, takes the perimeter from the map's
impact packets and the commits since the last known good, and sends at most
three hypotheses to the specialist auditor of each mechanism, each in isolation
and blind to the others. The strongest survivor gets a reproduction test from
`testing:test-writer`, checked against the parent of a suspect commit, and
`git bisect run` finds the first bad commit when none is confirmed. Execution
stays in a disposable worktree or the project's own runner; there is no
interactive debugger. The verdict is `demonstrated`, `probable` or `open`, and a
correction goes through the task cycle with the reproduction as its oracle.

#### Why the pipeline is shaped this way

The method units state the rules; the reasons live here, so a reviewer's context
holds what it must do rather than why.

- **Two derivations, not one consulted N times.** Phase 1c derives the premises
  blind to the Codebase Map so that the review has a second observer. The join in
  Phase 1d, not the premise auditor, compares the two: a deriver that compared its
  own output could not demonstrate its blindness.
- **Phase 0c stays out of raw mode.** Its leads file, given to N reviewers, is
  itself shared context. Kept alive under `--no-context`, it would make findings
  legitimately `shared-context`, wake Lens 0, and stop raw mode reproducing the
  pre-pipeline behaviour it exists to provide.
- **Phase 0c never reads a Codebase Map run, old ones included.** An earlier run is
  still a Codebase Map derivation, and reading it would contaminate the one artifact
  that has to be independent of it.
- **No substitute for the analyst.** A freelance worker imitating the analysis would
  not produce the file names and section anchors that the interconnect mapper and
  `logic-integrity-auditor` depend on; a missing analysis is a broken installation.
- **Missing is not Disputed.** Collapsing them would drain `disputed` of its meaning,
  which is that two derivations reached incompatible conclusions and a reviewer must
  settle it. And without the duty to keep what one branch found when the other was
  silent, the completeness of the Codebase Map's discovery would become the next
  shared premise.

### The code-review variant

The variant stays inside `review-method` for callers that name it. `/daodan:review-changes` does not run it: its light review is one unit, `references/light.md`, with one reviewer chosen by the target's kind (see the roster above).

Unified code review that auto-detects scope: uncommitted/staged changes, recent commits, PR number, or branch diff. The canonical `review-method` selects twelve core review slots: always-on code audit (A), security (B), lite dead-code and VCS hygiene scoped to the diff (B2), and git history (E), plus conditional UI races (C), testing (F), API contracts (G), data migrations (H), structural entropy (J), temporal resilience (L), data integrity (M) and resource lifecycle (N). Named specialists retain their owner-qualified roles; inline history, hygiene, verification, critic and fix tasks use `project-protocol:isolated-worker`. The same review selects up to three additional stack dimensions: React performance, TypeScript type safety and platform integration. It uses their canonical specialist roles in the same batch and accounts for them before consolidation; the user chooses no second review bundle.

Agent J is the structural-entropy review, `abstraction-architect:abstraction-architect-agent`. It runs whenever the diff adds code (at least one function, method, class, module, constant table, or block longer than roughly five lines) and is skipped only for diffs that are purely deletions, renames, formatting, or config edits. It is the one agent whose question is about the rest of the codebase: it takes the diff as an anchor and asks whether the diff adds a second place where a concept the codebase already owns now lives. It covers seven dimensions over two evidence tracks. The knowledge track (duplicated domain knowledge, competing sources of truth, redundant representation, duplicated or derivable state) is judged by semantic identity and ownership, seeded by `.abstraction-architect/concept-index.json` when one exists; without it the agent works from diff-anchored discovery and says so. The form track (missed unification, prior art available, abstraction fitness) is judged by recurrence, and the Rule of Three applies only to missed unification. `code-auditor` keeps the single-file abstraction smells.

**Options**, bound by a caller that names the variant: `[PR number | --branch <name> | --commits N] [--fix] [--commit] [--auto-comment] [--strict] [--fast] [--rigorous]`. `--strict` makes any Critical finding force a `Not ready` verdict; `--fast` skips the verification panel and the completeness critic; `--rigorous` verifies every finding above the confidence floor, ignoring the cost guard.

**Fix authorizations:** `--fix` applies scoped fixes and verifies the candidate without committing. `--commit` implies `--fix` and permits commits: one per fix or batch in Step 7b, one per phase in Step 7c. Bulk application cleanup is commit-only and requires an exclusively owned clean isolated worktree. Each phase captures its recovery SHA before editing, gates the candidate before committing and preserves earlier successful phases. Recovery follows project-protocol; published changes require an authorized revert.


---

### Dead code and cleanup

There is no cleanup command of this plugin; `/daodan:tidy-repo` previews every owner's cleanup together. The capability is split by scope, so you never install or invoke anything extra to get it.

| Scope | Where it runs | Coverage |
|---|---|---|
| **Lite** | The code-review variant (Agent B2) and the pr-review variant, on the changed files | Dead code (Knip for TS/JS, vulture and ruff for Python), plus the `repo-hygiene:repo-hygiene` skill's VCS checks at its lite profile |
| **Full** | The branch review (`/daodan:review-branch`), always-on `cleanup-auditor` dimension across the whole codebase | All five dimensions: dead code, orphan assets, dependency and barrel-file hygiene, stale documentation, lifecycle archaeology. Workspace hygiene is the separate always-on `repo-hygiene:workspace-auditor` dimension in the same pipeline |
| **Removal** | `application-cleanup-method` with commit authorization: Step 7c of the code-review variant, or `/daodan:tidy-repo` | Five phases lowest-risk-first (`brand`, `assets`, `deps`, `exports`, `docs`), one commit each, build and test gate between phases; failure recovery uses the captured pre-phase SHA in an exclusively owned clean worktree |

Removal safety comes from the Step 7c rules: clean working tree before starting, phase isolation so each step is independently revertible, a confirmation Grep returning zero results before any delete, no removal of anything reached through dynamic imports or framework conventions, and explicit user approval for Python functions and classes given vulture's false-positive rate. The `docs` phase is report-only unless removal is explicitly opted into.

The lite pass runs the tools directly: Knip for TS/JS (with `tsc --noUnusedLocals --noUnusedParameters` when Knip is absent), ruff and vulture for Python. The pr-review variant skips a tool that is not installed rather than installing it, and notes the skip. Workspace tidying decided by the filesystem and git alone (committed build output, `.gitignore`, scratch directories, git state) belongs to the `repo-hygiene:repo-hygiene` tidy method (`/daodan:tidy-repo`), not to Step 7c.

The former cleanup-dead-code command was removed in plugin 7.0.0 (marketplace 16.0.0). Its detection duplicated `cleanup-auditor` and its removal machinery moved into Step 7c above.

---

### The pr-review variant (`/daodan:review-branch` on a pull request)

Analyze current branch changes, generate a PR description with risk assessment and review checklist, and optionally create the PR via `gh`.

| | |
|---|---|
| **Options** | `[--base <branch>] [--create] [--split-check] [--strict-mode]`, parsed by `review-preparation` |

- `--base <branch>` sets the base branch (default `main`, falling back to `master` when `main` does not exist)
- `--create` shows the full PR description for approval, then runs `gh pr create`; it never pushes an unpushed branch without asking
- `--split-check` adds PR split suggestions (they are also added whenever the PR exceeds 500 lines)
- `--strict-mode` recommends splitting or addressing security findings before creating the PR when critical risk factors are detected
- Runs the lite dead-code and VCS-hygiene pass over the diff and reports it in its own `## Hygiene` section; every finding names its owner-qualified phase (`senior-review:application-cleanup-method` phase `exports` for dead code, the `repo-hygiene:repo-hygiene` tidy phase `garbage` or `gitignore` for what the filesystem and git decide). It never removes anything
- Checks `CLAUDE.md` alignment: when the changes make the project's `CLAUDE.md` outdated, the description gets a `## CLAUDE.md Updates Needed` section


---

**Related:** the branch review uses these agents directly | [repo-hygiene](repo-hygiene.md) (workspace tidying, `/daodan:tidy-repo`) | [typescript-development](typescript-development.md) (Knip for dead code) | [python-development](python-development.md) (vulture/ruff for dead code)

<!-- daodan:reference:start -->
## Source-derived reference

Generated by `python scripts/sync_plugin_docs.py`. Edit the kernel and regenerate
this block; keep explanations above it. `--check` detects stale references.

**Version:** `16.2.0`. **Source:** [plugin.toml](<../../plugins/senior-review/plugin.toml>).

### Required dependencies

Every listed plugin dependency is mandatory. Transitive requirements remain
mandatory when using this plugin alone. The local closure includes this plugin.

| Requirement | Plugins |
|---|---|
| Direct local | [abstraction-architect](<abstraction-architect.md>), [codebase-map](<codebase-map.md>), [dependency-audit](<dependency-audit.md>), [platform-engineering](<platform-engineering.md>), [project-protocol](<project-protocol.md>), [python-development](<python-development.md>), [react-development](<react-development.md>), [repo-hygiene](<repo-hygiene.md>), [report-rendering](<report-rendering.md>), [skill-catalog](<skill-catalog.md>), [testing](<testing.md>), [typescript-development](<typescript-development.md>) |
| Direct external | None |
| Local closure (13) | [abstraction-architect](<abstraction-architect.md>), [codebase-map](<codebase-map.md>), [dependency-audit](<dependency-audit.md>), [platform-engineering](<platform-engineering.md>), [project-protocol](<project-protocol.md>), [python-development](<python-development.md>), [react-development](<react-development.md>), [repo-hygiene](<repo-hygiene.md>), [report-rendering](<report-rendering.md>), [senior-review](<senior-review.md>), [skill-catalog](<skill-catalog.md>), [testing](<testing.md>), [typescript-development](<typescript-development.md>) |
| External closure (2) | `developer-essentials@claude-code-workflows`, `mattpocock-skills@mattpocock` |

External bundles are separate upstream installations, not copied local skills.
See [host setup](<../hosts.md>) for selection and availability requirements.

**Required capabilities:** `repository.read`, `shell.execute`, `repository.write`, `contexts.isolate`, `roles.dispatch`.
**Optional capabilities:** `execution.parallel`.
Optional capabilities are host mechanisms, not optional local plugin dependencies.

### Registered components

Names below are kernel IDs. Host entry points and paths follow the adapter
mapping in [the host reference](<../hosts.md>).
The source links carry the complete instructions and accepted arguments.

| Kind | ID | Purpose and trigger | Source |
|---|---|---|---|
| Skill | `senior-review:defect-taxonomy` | 16 macro-categories and 140+ subcategories of source-code failure modes, with CWE and OWASP mappings, fix patterns, and review frameworks. TRIGGER WHEN: an audit needs structured defect classification, a detection strategy, or severity calibration; loaded by code-auditor, security-auditor, and ui-race-auditor. | [defect-taxonomy](<../../plugins/senior-review/skills/defect-taxonomy/SKILL.md>) |
| Skill | `senior-review:review-quality-gates` | Verification panel, completeness critic, pipeline conventions and shared-context provenance rules for multi-reviewer consolidation. TRIGGER WHEN: running team-review (/daodan:review-branch) or code-review quality gates, or consolidating findings from parallel reviewers. | [review-quality-gates](<../../plugins/senior-review/skills/review-quality-gates/SKILL.md>) |
| Skill | `senior-review:review-method` | Unified review engine: the light review and the branch review (variants team-review and pr-review, and code-review), including signal-selected stack specialists. TRIGGER WHEN: the user asks to review current changes, a commit, a file, a plan, a specification, a document, a branch or a pull request for defects, or /daodan:review-changes, /daodan:review-branch or a lifecycle review phase runs a review. DO NOT TRIGGER WHEN: establishing the root cause of a reported failure without reviewing an artifact (use investigation-method), or removing dead code (use application-cleanup-method). | [review-method](<../../plugins/senior-review/skills/review-method/SKILL.md>) |
| Skill | `senior-review:review-preparation` | Prepare the existing code, team or PR review inputs without writing another detection prompt. Load before dispatching reviewers in senior-review or project-lifecycle. | [review-preparation](<../../plugins/senior-review/skills/review-preparation/SKILL.md>) |
| Skill | `senior-review:review-consolidation` | Consolidate native review findings with evidence provenance, delivery accounting and adversarial verification. Load when consolidating code-review, team-review or pr-review results. | [review-consolidation](<../../plugins/senior-review/skills/review-consolidation/SKILL.md>) |
| Skill | `senior-review:application-cleanup-method` | Apply accepted application-subtraction findings with isolated phases and snapshot-bound build/test gates. Load when running /daodan:tidy-repo, code-review Step 7c or lifecycle cleanup. | [application-cleanup-method](<../../plugins/senior-review/skills/application-cleanup-method/SKILL.md>) |
| Skill | `senior-review:investigation-method` | Investigate an observed error, bug or strange behavior to a demonstrated cause, without fixing it: facts, perimeter from the map, isolated hypotheses, a reproduction test, bisection. TRIGGER WHEN: the user reports an error, regression or strange behavior whose cause is unknown and wants it investigated, a coordinator investigates a problem, or a bug fix starts without a known cause. DO NOT TRIGGER WHEN: assessing a change or artifact for defects (use review-method), or the root cause is already established with evidence. | [investigation-method](<../../plugins/senior-review/skills/investigation-method/SKILL.md>) |
| Role | `senior-review:api-contract-auditor` | Auditor for drift between declared API contracts and their implementation. TRIGGER WHEN: checking OpenAPI/Swagger, JSON Schema, GraphQL SDL, gRPC .proto, AsyncAPI, TypeScript DTOs or Pydantic models against code, or reviewing API surface changes. DO NOT TRIGGER WHEN: no contract file exists (use code-auditor), cross-service runtime flows (use distributed-flow-auditor), or internal domain invariants (use logic-integrity-auditor). | [api-contract-auditor](<../../plugins/senior-review/roles/api-contract-auditor.md>) |
| Role | `senior-review:chicken-egg-detector` | Detects the chicken-and-egg cycle where component A needs B ready while B needs A: cold-start hangs, deadlocks, hidden temporal coupling. TRIGGER WHEN: the target involves startup ordering, initialization sequences, bootstrap or config loading, service discovery, or migration dependencies; or the system comes up correctly only by luck. DO NOT TRIGGER WHEN: the concern is runtime flow with no initialization phase (use distributed-flow-auditor). | [chicken-egg-detector](<../../plugins/senior-review/roles/chicken-egg-detector.md>) |
| Role | `senior-review:cleanup-auditor` | Application-hygiene auditor for dead code, orphan assets, unused dependencies, stale docs and migration/debug leftovers. TRIGGER WHEN: dispatched by senior-review's review method under /daodan:review-changes or /daodan:review-branch, by /daodan:tidy-repo or /daodan:check-health, or asked for a technical-debt, dead-code, orphan-asset or unused-dependency audit. DO NOT TRIGGER WHEN: applying removals (use senior-review:application-cleanup-method under commit authorization, from /daodan:tidy-repo), filesystem/git tidying (use repo-hygiene:workspace-auditor), or single-language scans (use typescript-development:knip or python-development:python-dead-code). | [cleanup-auditor](<../../plugins/senior-review/roles/cleanup-auditor.md>) |
| Role | `senior-review:code-auditor` | Hunts coupling violations, broken abstractions, resource leaks, stale caches, and anti-patterns. TRIGGER WHEN: the user asks for a code review, architecture audit, quality scoring, failure-path analysis, or pattern consistency check. DO NOT TRIGGER WHEN: the task is security-specific auditing (use security-auditor). | [code-auditor](<../../plugins/senior-review/roles/code-auditor.md>) |
| Role | `senior-review:data-integrity-auditor` | Persistence-layer reviewer for partial writes, read-modify-write races, missing DB uniqueness constraints and cache-database divergence. TRIGGER WHEN: target touches schemas, models, ORM entities, repositories, raw SQL, caches or transaction boundaries. DO NOT TRIGGER WHEN: domain rules/state machines (use logic-integrity-auditor) or cross-service message flows (use distributed-flow-auditor). | [data-integrity-auditor](<../../plugins/senior-review/roles/data-integrity-auditor.md>) |
| Role | `senior-review:distributed-flow-auditor` | Hunts cascading timeout violations, missing idempotency, broken saga compensation, message ordering bugs, and split-brain risks. TRIGGER WHEN: the target spans microservices, agent systems, or multiple modules and the question is cross-service: request flow tracing, contract mismatch between producer and consumer, or integration-boundary review. | [distributed-flow-auditor](<../../plugins/senior-review/roles/distributed-flow-auditor.md>) |
| Role | `senior-review:logic-integrity-auditor` | Cross-component reviewer for ordering, idempotency, state machines, terminal states and domain invariants in .team-review/02-interconnect.md, or in a scoped semantic context when no interconnect map exists. TRIGGER WHEN: Phase 2 of senior-review's branch review (/daodan:review-branch) runs, a lite review supplies a scoped semantic context, or asked for a logic, contract or invariant audit. DO NOT TRIGGER WHEN: style/lint review (use code-auditor), security-only review (use security-auditor), or neither an interconnect map nor a scoped semantic context is supplied (report the missing prerequisite; in team review, semantic-interconnect-mapper can build the map). | [logic-integrity-auditor](<../../plugins/senior-review/roles/logic-integrity-auditor.md>) |
| Role | `senior-review:premise-auditor` | Derives independent code claims (Mode 1, blind to shared maps), challenges load-bearing finding premises (Mode 2, Lens 0) and checks what a plan, record or document claims about the code (Mode 3). TRIGGER WHEN: Phase 1c of senior-review's branch review (/daodan:review-branch) runs, the verification panel spawns Lens 0 for a finding premise, or a review of a plan, a specification or a document dispatches the claim check. DO NOT TRIGGER WHEN: hunting defects (use dimension auditors) or building the interconnect map (use codebase-map:semantic-interconnect-mapper). | [premise-auditor](<../../plugins/senior-review/roles/premise-auditor.md>) |
| Role | `senior-review:resource-lifecycle-auditor` | Reviewer for resource acquisition and release across success, error and cancellation paths: leaks, double-release, use-after-release and unbounded pools. TRIGGER WHEN: target acquires file handles, sockets, streams, DB connections, subprocesses, listeners, locks, threads, timers or GPU/native memory. DO NOT TRIGGER WHEN: behavior over time after a leak (use temporal-resilience-auditor), memory-safety exploitation (use security-auditor), or general architecture (use code-auditor). | [resource-lifecycle-auditor](<../../plugins/senior-review/roles/resource-lifecycle-auditor.md>) |
| Role | `senior-review:security-auditor` | Attacker-mindset pass over the target: assumes it is exploitable and proves it. TRIGGER WHEN: the user asks for a security review, SAST audit, OWASP or CWE analysis, secret-leak scan, or an authentication or authorization code review; injection vectors, auth bypasses, crypto mistakes, or missing security headers; the target exposes URLs, routes or functions to untrusted callers; code reads or returns data by a caller-supplied ID (IDOR / data theft); code checks permissions, roles or ownership; or code creates, verifies or destroys logins and sessions. DO NOT TRIGGER WHEN: the concern is general code quality (use code-auditor) or infrastructure and network security (use platform-reviewer). | [security-auditor](<../../plugins/senior-review/roles/security-auditor.md>) |
| Role | `senior-review:temporal-resilience-auditor` | Reviewer for failure-over-time defects: missing backoff/caps, silent subsystem death, uncleared guards, notification floods and clock hazards. TRIGGER WHEN: reviewing timers, schedulers, polling loops, retry/reconnect logic, queues, cron jobs, background workers or watchdogs. DO NOT TRIGGER WHEN: startup/bootstrap cycles (use chicken-egg-detector), cross-service timeout chains (use distributed-flow-auditor), or UI rendering races (use ui-race-auditor). | [temporal-resilience-auditor](<../../plugins/senior-review/roles/temporal-resilience-auditor.md>) |
| Role | `senior-review:ui-race-auditor` | Framework-agnostic UI timing analyst: React, Angular, Vue, Qt, GTK, Flutter, SwiftUI, Electron, Tauri. TRIGGER WHEN: races between async data loading, layout, event handlers, and programmatic scroll, focus, or resize; scroll position corruption, sticky or auto-scroll breakage, focus theft, layout shift, stale measurement closures, layout-dependent reads racing incomplete renders. | [ui-race-auditor](<../../plugins/senior-review/roles/ui-race-auditor.md>) |

### Host exports

Package paths and coordination are derived from the host adapters. `native`
and `adapted` describe bindings, not successful installed-host execution.

The selected strategy is an adapter binding even for a flat workflow body.
A dispatch harness is rendered only for declared method workers, task-specific
workers or phase fan-out; the host reference explains the entry artifacts.

| Host | Package | Binding | Selected workflow strategy |
|---|---|---|---|
| claude | [exports/claude/plugins/senior-review](<../../exports/claude/plugins/senior-review>) | `native` | No workflow entry points |
| copilot | [exports/copilot/plugins/senior-review](<../../exports/copilot/plugins/senior-review>) | `native` | No workflow entry points |
| codex | [exports/codex/plugins/senior-review](<../../exports/codex/plugins/senior-review>) | `adapted` | No workflow entry points |
| pi | [exports/pi/plugins/senior-review](<../../exports/pi/plugins/senior-review>) | `adapted` | No workflow entry points |
| opencode | [exports/opencode/plugins/senior-review](<../../exports/opencode/plugins/senior-review>) | `native` | No workflow entry points |

### Additional shipped contracts and mechanisms

- Exported shared contract: [contracts/review-brief.toml](<../../plugins/senior-review/contracts/review-brief.toml>).
- Exported shared contract: [contracts/reviewer-binding.toml](<../../plugins/senior-review/contracts/reviewer-binding.toml>).
- Exported shared contract: [contracts/reviewer-selection.toml](<../../plugins/senior-review/contracts/reviewer-selection.toml>).
- Exported shared contract: [contracts/evidenced-finding.toml](<../../plugins/senior-review/contracts/evidenced-finding.toml>).
- Exported shared contract: [contracts/reviewer-result.toml](<../../plugins/senior-review/contracts/reviewer-result.toml>).
- Exported shared contract: [contracts/delivery-ledger.toml](<../../plugins/senior-review/contracts/delivery-ledger.toml>).
- Exported shared contract: [contracts/final-report.toml](<../../plugins/senior-review/contracts/final-report.toml>).

<!-- daodan:reference:end -->

## Available domain knowledge

Preparation also uses the required skill-catalog provider to select knowledge for
the exact affected scopes, across any classified available language/framework/domain.
The coordinator records provider/version, content fingerprints, scope evidence and
assigned worker delivery IDs. Existing auditors consume relevant knowledge with their
canonical briefs; several skills may support one auditor. A domain question without
a selected lens can use the already declared isolated-worker within the same budget.

Knowledge usage and on-demand reference hashes are checked during consolidation.
Missing or stale selected inputs are failed coverage. Unknown inventory/classification
and unmatched scope remain explicit gaps in the single report. Existing React,
TypeScript and platform roles and required providers retain their native contracts;
knowledge selection supplies additional domain competence without a second workflow.
