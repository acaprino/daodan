# Senior Review Plugin

> Catch bugs before they ship. Twelve specialized agents: eleven review code quality, security, UI timing, distributed flows, startup cycles, temporal resilience (failure-over-time), data integrity (persistence semantics), resource lifecycle (ownership and release), cross-component logic integrity, formal API contracts, and codebase hygiene in parallel, and the twelfth, `premise-auditor`, derives the code's claims a second time, independently, and attacks the premises findings stand on. The reviewers read a shared contract/invariant map built by `codebase-xray:semantic-interconnect-mapper`, which is why they find bugs that are invisible from local-only inspection. Backed by a comprehensive defect taxonomy knowledge base with 140+ defect patterns and CWE/OWASP mappings. `/senior-review:team-review` runs all of it as a single pipeline, with an adversarial verification panel and a completeness critic as quality gates before the report ships.

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
- Activated in `/senior-review:team-review` and `/senior-review:code-review` (Agent L) by long-running/scheduled-execution signals in the diff
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
- Activated by persistence signals in `/senior-review:team-review` and as Agent M of `/senior-review:code-review`
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
- Conditional, never always-on; activated by acquisition signals in `/senior-review:team-review` and as Agent N of `/senior-review:code-review`
- References `defect-taxonomy` skill (`memory-resources.md`, `concurrency-state.md`)

---

### `logic-integrity-auditor`

Adversarial reviewer that hunts for violations of contracts, invariants, assumptions, domain rules, ordering, idempotency, and state machines documented in the interconnect map. Catches bugs no local-only reviewer can see: logic drift across components, implicit contracts silently broken, terminal states mutated, retry paths double-committing.

| | |
|---|---|
| **Model** | `inherit` |
| **Use for** | `/senior-review:team-review` Phase 2 (always-on in the review preset); logic/contract/invariant audit of code with an associated interconnect map |

**Invocation:**
```
Used automatically by /senior-review:team-review; requires .team-review/02-interconnect.md (produced by semantic-interconnect-mapper)
```

**Methodology:** Reads the interconnect map + target files, proves violations of documented contracts / invariants / domain rules / assumptions. Stops and reports if interconnect map is absent (precondition failure).

---

### `premise-auditor`

Second, independent derivation of the code's claims, and attack on the load-bearing assumptions behind findings built from a common artifact. It exists because a pipeline that derives one premise and then explores it with N agents has one observer, not N.

| | |
|---|---|
| **Model** | `inherit` |
| **Tools** | Read, Write, Glob, Grep, Bash |
| **Use for** | `/senior-review:team-review` Phase 1c (independent derivation) and Lens 0 of the adversarial verification panel (premise challenge). It does not hunt defects |

**Invocation:**
```
Used automatically by /senior-review:team-review; the spawning prompt names the mode
```

**Methodology:**
- Two modes with different inputs, never blended
- **Mode 1, independent derivation (Phase 1c):** blind to `.codebase-xray/` in any form and to `.team-review/02-interconnect.md`; if its prompt paraphrases an X-ray conclusion it reports the contamination instead of proceeding. It establishes what is true about the concepts the diff touches by reading callers, callees, tests and the documents the knowledge leads point at, hunts for multiplicity (a second path where the code appears to have one), and writes `.team-review/01b-independent-claims.md`. It derives only: no comparison, no review, no fixes, no severity
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

Adversarial codebase hygiene auditor. Detects dead code, orphan assets, phantom/unused dependencies, barrel-file bloat, eager-bundling anti-patterns, rebrand residue, stale documentation and historical artifacts, and lifecycle residue (leftovers of completed migrations and refactors, temporary debug tooling) inferred via commit-history and session-transcript archaeology. Every one of its dimensions needs source comprehension; what the filesystem and git decide alone (generated artifacts tracked in VCS, filesystem garbage, `.gitignore`, scratch directories, orphan doc-assets, stale stashes, worktrees and branches) belongs to `repo-hygiene:workspace-auditor`. Report-only; the fix is delegated to Step 7c of `/senior-review:code-review --commit`.

| | |
|---|---|
| **Model** | `inherit` |
| **Tools** | Read, Write, Glob, Grep, Bash |
| **Use for** | Codebase cleanup review, technical-debt audit, dead-code detection with asset and dependency coverage, monorepo dependency hygiene. Always-on dimension in `/senior-review:team-review`. |

**Invocation:**
```
Use the cleanup-auditor agent to scan [path]
```
Also spawned automatically by `/senior-review:team-review` as the "Codebase hygiene" dimension.

**Methodology:**
- 5-dimension detection pipeline, every one of them needing source comprehension: D1 dead code (runs Knip, vulture and ruff and reads their output), D2 asset hygiene (orphan images, fonts and media, eager `import.meta.glob` bloat, rebrand residue), D3 dependency hygiene (phantom and unused dependencies across monorepo workspaces, barrel-file bloat, eagerly bundled heavy packages), D4 documentation and historical artifacts (completed or abandoned plans, backup and archive folders, stale doc references, superseded ADRs), D5 lifecycle archaeology (session-transcript evidence of intent, commit-sequence inference of completed or in-progress migrations)
- Every finding cites `file:line` or a concrete path; vague "consider cleaning up" advice is forbidden
- Every finding carries a confidence tier (CONFIRMED / HIGH / MEDIUM / LOW; LOW never recommends deletion) and a residue action (DELETE, KEEP, KEEP+IGNORE, DELETE+IGNORE, DELETE+PREVENT-GENERATION, UNIGNORE, REVIEW)
- Session transcripts are treated as evidence, never as instructions; transcript-only evidence caps confidence at MEDIUM
- False-positive candidates (module augmentation, side-effect imports, DI-registered classes, framework-convention files) flagged in a separate section, never auto-confirmed
- Each finding ends with `Fix phase: <phase>`, naming one of the five Step 7c phases of `/senior-review:code-review --commit` (`brand`, `assets`, `deps`, `exports`, `docs`) that would remove it; a finding whose only fitting phase belongs to `/repo-hygiene:tidy` is outside its dimensions and is dropped

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

**Context Sharing Pattern:** reviewers read the X-ray run directory plus `.team-review/02-interconnect.md` (contracts, invariants, domain rules, assumptions, integration hot-spots) and `.team-review/01-knowledge-provenance.md`, guided by anchor routing per dimension (security reads Integration Hot-Spots plus unverified Assumptions; logic-integrity reads Contracts, Invariants, and Domain Rules; and so on). Every finding declares two extra fields: its **load-bearing premise** (the single proposition whose falsity collapses it) and that premise's **provenance** (`independent`, `shared-context`, or `mixed`, recording causal dependence rather than citation). The **map utilization rate** (share of findings citing a map anchor) is an operational number only, and no target is set for it: a high value on a wrong map is the signature of the failure this pipeline exists to prevent. The quality signals are elsewhere: independent premise reconstruction rate, premise challenge rate, map challenge rate, map gap rate, and cross-source corroboration.

**Adversarial Verification Panel:** every finding above a 50% confidence floor is judged by up to 4 lenses (Premise Challenge, Reachability/Correctness, False-Positive Causes, Severity Calibration). **Lens 0 is a veto, gated and first.** It runs on findings whose premise provenance is `shared-context` or `mixed`, and on any finding whose declared premise carries a universal or negative quantifier (`no`, `never`, `cannot`, `always`, `only`) at any provenance, since an over-scoped premise can be born independently as easily as it can be inherited. It attacks the premise rather than the finding and returns `REFUTED` only with a `file:line` counterexample, stating whether that counterexample kills the PREMISE itself or only a piece of shared SUPPORT: killing the premise discards the finding as `filtered: premise-refuted` without spending lenses 1-2, while `UNCERTAIN` proceeds tagged `premise-contested`. It never kills a finding by failing, since error, malformed output and evidence-free refutation all collapse to `UNCERTAIN`. Lenses 1-2 then run in parallel; lens 3 is **gated on survival** (calibrating a finding about to be discarded is spend for nothing, and the gate cuts roughly a third of verifier calls). A finding survives if at least 2 of lenses 1-2 vote REAL, is discarded (`filtered`) if at least 2 vote FALSE_POSITIVE, and survives `contested` on a tie. Final severity comes from lens 3's vote. A cost guard (a finding-count proxy, not a token budget) narrows verification to Critical/High plus an uncertainty band once more than 25 findings survive dedup, unless `--rigorous` is passed; `--fast` skips the panel entirely.

**Evidence Classes:** any finding that quantifies damage labels the number `measured` (harness, simulation, logs, with the method stated) or `derived` (computed by reading the code). A `derived` number alone cannot justify Critical severity, and no finding can be closed as acceptable ("bounded", "low traffic") without also answering the **user-visible-consequence question**: what does the user see, and when? "Nothing, silently" escalates severity rather than closing the finding.

**Delivery Gate:** every spawned reviewer is accounted for by a findings file, an explicit no-findings report or a failed delivery. A silent reviewer is nudged once; collected partial output remains marked undelivered and the dimension is **degraded**, never presented as clean. Workspace cleanup uses the run's owned-file manifest and hashes, preserving preexisting files, foreign edits, unresolved evidence and resume data. An unchanged owned probe can be removed only after its conditions, commands, outcomes and limitations are retained in the report and its evidence references still resolve. Persistent run retention belongs to the caller's consolidate path.

**Completeness Critic:** one agent checks coverage against a fixed gap taxonomy (dimensions warranted but not run, in-scope files cited by no finding, unverified interconnect assumptions untouched by any finding, high-risk hot-spots with zero findings, and findings closed on a metric alone without a stated user-visible consequence) and may trigger one bounded follow-up round for the single highest-risk gap it names.

**Reviewer Pipeline Conventions:** every Phase 2 reviewer carries a scope budget (stops after ~15 file reads without a finding), a no-findings protocol (a clean "examined X, Y, Z: no issues" report is valid, not a failure), and a `## Cross-Reviewer Notes` section for observations that belong to another dimension.

---

### Reusable review methods

`review-preparation` resolves the variant's scope, flags, exact snapshot and shared context. `review-method` owns the code-review, team-review and pr-review procedures. `review-consolidation` accounts for core and extension deliveries, applies the same provenance and verification rules, and writes the native report with a `project-result` envelope. The seven review-domain schemas retain their own finding and evidence meanings; [project-protocol](project-protocol.md) owns operational state and candidate validation.

`application-cleanup-method` exposes the former Step 7c subtraction procedure to reviews and lifecycle plans. Its inputs include accepted findings and severities, completed targeted fixes where needed, a clean exclusively owned isolated worktree, meaningful build/test gates and commit authorization. It does not add another auditor.

## Commands

### `/senior-review:team-review`

Multi-dimensional code review as a **6-phase pipeline**: independent evidence discovery and context building first, so reviewers hunt cross-component logic bugs, not just what's visible from local inspection.

**Execution:** dispatch, isolation and result collection come from the host harness, so nothing beyond `senior-review`'s own dependencies is needed. Every reviewer runs in its own context, exactly the selected dimensions are dispatched once each, and every reviewer is recorded delivered or failed before anything is consolidated. If the host cannot run reviewers in isolated contexts, the command stops and says so.

| | |
|---|---|
| **Invoke** | `/senior-review:team-review <target> [--reviewers auto\|security,performance,...] [--base-branch main] [--all] [--deep] [--no-context] [--fast] [--rigorous]` |
| **Artifact dir** | `.team-review/` (state, scope, interconnect map, per-dimension findings, consolidated report; preserved, not auto-deleted) |

**Pipeline:**

| Phase | What happens |
|-------|---------------|
| 0. Target resolution | Resolves `<target>` (path, git diff range, or PR number) and collects the diff |
| 0b. Context detection | Auto-selects review dimensions from changed files and codebase signals (skipped if `--reviewers` is explicit) |
| 0c. Review evidence discovery | Inline. Discovers what evidence this review needs from the project's own indexes and tests, forbidden from reading `.codebase-xray/` in any form including prior runs, and writes the immutable `.team-review/01a-review-knowledge-leads.md` |
| 1a. X-ray analysis | Runs the `codebase-xray:analyze` **workflow** in the orchestrating context, not as a dispatched worker (`--depth=lite` by default, full with `--deep`); halts the pipeline if it produces no output |
| 1c. Independent premise derivation | `premise-auditor` in mode 1, spawned in the same turn as 1a and blind to its output, writes `.team-review/01b-independent-claims.md`. A second observer, not the same observer consulted twice |
| 1d. Knowledge reconciliation | Inline join of 01a, 01b and X-ray's `knowledge/documentation-leads.md` into `.team-review/01-knowledge-provenance.md`, keeping `Missing` and `Disputed` strictly apart |
| 1b. Interconnect mapping | `semantic-interconnect-mapper` builds `.team-review/02-interconnect.md`, turning every contradiction between the two derivations into a `disputed` row |
| 2. Adversarial review | Spawns one reviewer per dimension in parallel, each reading the X-ray run directory, the interconnect map and the knowledge provenance, and declaring the load-bearing premise and provenance of every finding |
| 3. Monitor and collect | Delivery gate: consolidation does not start until every spawned reviewer has delivered its findings file or an explicit no-findings report; a silent reviewer is nudged once, then salvaged and reported as degraded |
| 4. Consolidation | Deduplicates findings, resolves severity conflicts, weighs agreement by premise provenance (independent agreement corroborates, shared-premise agreement is an echo), collects `[MAP-GAP]` findings as mapper coverage gaps, organizes by severity; writes `.team-review/99-consolidated.md` |
| 4b. Adversarial verification | Quality gate, see `review-quality-gates` above (skipped with `--fast`) |
| 4c. Completeness critic | Quality gate, see `review-quality-gates` above (skipped with `--fast`) |
| 5. Report & cleanup | Compare the complete workspace baseline and owned-artifact manifest; preserve conclusions before removing unchanged owned probes. Report map utilization, premise metrics, corroboration and echoes; preserve `.team-review/` for later reference |

**Always-on dimensions:** security, architecture, logic integrity (skipped under `--no-context`), codebase hygiene (`cleanup-auditor`), workspace hygiene (`repo-hygiene:workspace-auditor`: filesystem garbage, generated artifacts tracked in VCS, `.gitignore` completeness, scratch and pipeline-output directories, orphan doc-assets, git auxiliary state; disjoint from codebase hygiene by construction).

**Conditional dimensions** use change signals to select UI races, distributed flows, circular dependencies, temporal resilience, data integrity, resource lifecycle and API contracts. Structural entropy dispatches `abstraction-architect:abstraction-architect-agent`; test quality dispatches `testing:test-suite-auditor`. These are declared required providers. General performance uses code-auditor; data migrations use data-integrity-auditor. Logic findings about rules absent from the interconnect map retain `[MAP-GAP]` and mapper coverage limitations. React performance, TypeScript type safety and platform integration are selected from the relevant package and target signals by the same preparation method. Their canonical roles remain in [react-development](react-development.md), [typescript-development](typescript-development.md) and [platform-engineering](platform-engineering.md); one selection, delivery ledger, verification panel and report account for them alongside every other dimension. Missing required workers remain failed deliveries; generic verifier or critic tasks use an explicitly declared isolated worker, never substitute for a missing specialist.

```
/senior-review:team-review src/auth/                                # auto-detected dimensions
/senior-review:team-review main...HEAD --reviewers security,testing # explicit dimensions on a diff
/senior-review:team-review #42 --rigorous                           # PR review, verify every finding
/senior-review:team-review src/ --no-context                        # raw mode, no context phase
```

`--no-context` reproduces the pre-pipeline behavior: no context phase, no `logic-integrity-auditor`, reviewers see only the target and diff. Use it for quick scans or targets under roughly 100 LOC.

---

### `/senior-review:code-review`

Unified code review that auto-detects scope: uncommitted/staged changes, recent commits, PR number, or branch diff. The canonical `review-method` selects twelve core review slots: always-on code audit (A), security (B), lite dead-code and VCS hygiene scoped to the diff (B2), and git history (E), plus conditional UI races (C), testing (F), API contracts (G), data migrations (H), structural entropy (J), temporal resilience (L), data integrity (M) and resource lifecycle (N). Named specialists retain their owner-qualified roles; inline history, hygiene, verification, critic and fix tasks use `project-protocol:isolated-worker`. The same review selects up to three additional stack dimensions: React performance, TypeScript type safety and platform integration. It uses their canonical specialist roles in the same batch and accounts for them before consolidation; the user chooses no second review bundle.

Agent J is the structural-entropy review, `abstraction-architect:abstraction-architect-agent`. It runs whenever the diff adds code (at least one function, method, class, module, constant table, or block longer than roughly five lines) and is skipped only for diffs that are purely deletions, renames, formatting, or config edits. It is the one agent whose question is about the rest of the codebase: it takes the diff as an anchor and asks whether the diff adds a second place where a concept the codebase already owns now lives. It covers seven dimensions over two evidence tracks. The knowledge track (duplicated domain knowledge, competing sources of truth, redundant representation, duplicated or derivable state) is judged by semantic identity and ownership, seeded by `.abstraction-architect/concept-index.json` when one exists; without it the agent works from diff-anchored discovery and says so. The form track (missed unification, prior art available, abstraction fitness) is judged by recurrence, and the Rule of Three applies only to missed unification. `code-auditor` keeps the single-file abstraction smells.

**Invoke:** `/senior-review:code-review [PR number | --branch <name> | --commits N] [--fix] [--commit] [--auto-comment] [--strict] [--fast] [--rigorous]`. `--strict` makes any Critical finding force a `Not ready` verdict; `--fast` skips the verification panel and the completeness critic; `--rigorous` verifies every finding above the confidence floor, ignoring the cost guard.

**Fix flags:** `--fix` applies scoped fixes and verifies the candidate without committing. `--commit` implies `--fix` and permits commits: one per fix or batch in Step 7b, one per phase in Step 7c. Bulk application cleanup is commit-only and requires an exclusively owned clean isolated worktree. Each phase captures its recovery SHA before editing, gates the candidate before committing and preserves earlier successful phases. Recovery follows project-protocol; published changes require an authorized revert.

```
/senior-review:code-review                     # auto-detect: uncommitted changes or branch diff
/senior-review:code-review 42                  # review PR #42
/senior-review:code-review --commits 3         # review last 3 commits
/senior-review:code-review --branch feature    # review branch diff
/senior-review:code-review --auto-comment      # post findings as PR comments
/senior-review:code-review --fix               # apply fixes, run tests, no commits
/senior-review:code-review --commit            # apply fixes and commit; enables Step 7c cleanup
/senior-review:code-review --strict --rigorous # verify every finding; any Critical means Not ready
```

---

### Dead code and cleanup

There is no standalone cleanup command. The capability is split by scope, so you never install or invoke anything extra to get it.

| Scope | Where it runs | Coverage |
|---|---|---|
| **Lite** | `/senior-review:code-review` (Agent B2) and `/senior-review:pr-review`, on the changed files | Dead code (Knip for TS/JS, vulture and ruff for Python), plus the `repo-hygiene:repo-hygiene` skill's VCS checks at its lite profile |
| **Full** | `/senior-review:team-review`, always-on `cleanup-auditor` dimension across the whole codebase | All five dimensions: dead code, orphan assets, dependency and barrel-file hygiene, stale documentation, lifecycle archaeology. Workspace hygiene is the separate always-on `repo-hygiene:workspace-auditor` dimension in the same pipeline |
| **Removal** | `/senior-review:code-review --commit` via `application-cleanup-method` | Five phases lowest-risk-first (`brand`, `assets`, `deps`, `exports`, `docs`), one commit each, build and test gate between phases; failure recovery uses the captured pre-phase SHA in an exclusively owned clean worktree |

Removal safety comes from the Step 7c rules: clean working tree before starting, phase isolation so each step is independently revertible, a confirmation Grep returning zero results before any delete, no removal of anything reached through dynamic imports or framework conventions, and explicit user approval for Python functions and classes given vulture's false-positive rate. The `docs` phase is report-only unless removal is explicitly opted into.

The lite pass runs the tools directly: Knip for TS/JS (with `tsc --noUnusedLocals --noUnusedParameters` when Knip is absent), ruff and vulture for Python. `/senior-review:pr-review` skips a tool that is not installed rather than installing it, and notes the skip. Workspace tidying decided by the filesystem and git alone (committed build output, `.gitignore`, scratch directories, git state) belongs to `/repo-hygiene:tidy`, not to Step 7c.

The `/senior-review:cleanup-dead-code` command was removed in plugin 7.0.0 (marketplace 16.0.0). Its detection duplicated `cleanup-auditor` and its removal machinery moved into Step 7c above.

---

### `/senior-review:pr-review`

Analyze current branch changes, generate a PR description with risk assessment and review checklist, and optionally create the PR via `gh`.

| | |
|---|---|
| **Invoke** | `/senior-review:pr-review [--base <branch>] [--create] [--split-check] [--strict-mode]` |

- `--base <branch>` sets the base branch (default `main`, falling back to `master` when `main` does not exist)
- `--create` shows the full PR description for approval, then runs `gh pr create`; it never pushes an unpushed branch without asking
- `--split-check` adds PR split suggestions (they are also added whenever the PR exceeds 500 lines)
- `--strict-mode` recommends splitting or addressing security findings before creating the PR when critical risk factors are detected
- Runs the lite dead-code and VCS-hygiene pass over the diff and reports it in its own `## Hygiene` section; every finding names its owner-qualified phase (`/senior-review:code-review --commit` phase `exports` for dead code, `/repo-hygiene:tidy` phase `garbage` or `gitignore` for what the filesystem and git decide). It never removes anything
- Checks `CLAUDE.md` alignment: when the changes make the project's `CLAUDE.md` outdated, the description gets a `## CLAUDE.md Updates Needed` section

```
/senior-review:pr-review --create
/senior-review:pr-review --base develop --split-check
```

---

**Related:** `/senior-review:team-review` uses these agents directly | [repo-hygiene](repo-hygiene.md) (workspace tidying, `/repo-hygiene:tidy`) | [typescript-development](typescript-development.md) (Knip for dead code) | [python-development](python-development.md) (vulture/ruff for dead code)

<!-- daodan:reference:start -->
## Source-derived reference

Generated by `python scripts/sync_plugin_docs.py`. Edit the kernel and regenerate
this block; keep explanations above it. `--check` detects stale references.

**Version:** `14.0.0`. **Source:** [plugin.toml](<../../plugins/senior-review/plugin.toml>).

### Required dependencies

Every listed plugin dependency is mandatory. Transitive requirements remain
mandatory when using this plugin alone. The local closure includes this plugin.

| Requirement | Plugins |
|---|---|
| Direct local | [abstraction-architect](<abstraction-architect.md>), [codebase-xray](<codebase-xray.md>), [platform-engineering](<platform-engineering.md>), [project-protocol](<project-protocol.md>), [react-development](<react-development.md>), [repo-hygiene](<repo-hygiene.md>), [testing](<testing.md>), [typescript-development](<typescript-development.md>) |
| Direct external | None |
| Local closure (9) | [abstraction-architect](<abstraction-architect.md>), [codebase-xray](<codebase-xray.md>), [platform-engineering](<platform-engineering.md>), [project-protocol](<project-protocol.md>), [react-development](<react-development.md>), [repo-hygiene](<repo-hygiene.md>), [senior-review](<senior-review.md>), [testing](<testing.md>), [typescript-development](<typescript-development.md>) |
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
| Skill | `senior-review:review-quality-gates` | Verification panel, completeness critic, pipeline conventions, and the shared-context provenance rule. TRIGGER WHEN: running /senior-review:team-review quality gates; running /senior-review:code-review Steps 4b and 4c; consolidating or deduplicating findings from multiple parallel reviewers. DO NOT TRIGGER WHEN: single-reviewer style review with no consolidation phase, or generic team coordination (the host harness covers that). | [review-quality-gates](<../../plugins/senior-review/skills/review-quality-gates/SKILL.md>) |
| Skill | `senior-review:review-method` | Unified review engine for code-review, team-review and pr-review, including signal-selected stack specialists. | [review-method](<../../plugins/senior-review/skills/review-method/SKILL.md>) |
| Skill | `senior-review:review-preparation` | Prepare the existing code, team or PR review inputs without writing another detection prompt. | [review-preparation](<../../plugins/senior-review/skills/review-preparation/SKILL.md>) |
| Skill | `senior-review:review-consolidation` | Consolidate native review findings with evidence provenance, delivery accounting and adversarial verification. | [review-consolidation](<../../plugins/senior-review/skills/review-consolidation/SKILL.md>) |
| Skill | `senior-review:application-cleanup-method` | Apply accepted application-subtraction findings with isolated phases and snapshot-bound build/test gates. | [application-cleanup-method](<../../plugins/senior-review/skills/application-cleanup-method/SKILL.md>) |
| Role | `senior-review:api-contract-auditor` | Auditor for declared interfaces versus the code behind them. TRIGGER WHEN: checking OpenAPI, Swagger, JSON Schema, GraphQL SDL, gRPC .proto, AsyncAPI, TypeScript DTOs, or Pydantic models for drift against the implementation; a PR that touches an API surface; backwards compatibility before a release; or the interconnect map has a `## Contracts (formal)` section. DO NOT TRIGGER WHEN: there is no contract file (use code-auditor), the concern is cross-service runtime flow (use distributed-flow-auditor), or invariants beyond the contract surface (use logic-integrity-auditor). | [api-contract-auditor](<../../plugins/senior-review/roles/api-contract-auditor.md>) |
| Role | `senior-review:chicken-egg-detector` | Detects the chicken-and-egg cycle where component A needs B ready while B needs A: cold-start hangs, deadlocks, hidden temporal coupling. TRIGGER WHEN: the target involves startup ordering, initialization sequences, bootstrap or config loading, service discovery, or migration dependencies; or the system comes up correctly only by luck. DO NOT TRIGGER WHEN: the concern is runtime flow with no initialization phase (use distributed-flow-auditor). | [chicken-egg-detector](<../../plugins/senior-review/roles/chicken-egg-detector.md>) |
| Role | `senior-review:cleanup-auditor` | Always-on hygiene dimension of /senior-review:team-review. TRIGGER WHEN: the user asks for a cleanup review, technical-debt audit, dead code, orphan assets, unused dependencies, stale docs and historical artifacts, or leftovers of finished work (migrations, debug tooling). DO NOT TRIGGER WHEN: the user wants removal (use /senior-review:code-review --commit, Step 7c), workspace hygiene decided by the filesystem and git alone such as generated artifacts tracked in VCS, `.gitignore`, scratch directories, stale branches, stashes or worktrees (use repo-hygiene:workspace-auditor or /repo-hygiene:tidy), architecture or security review (use code-auditor or security-auditor), or one language only (use typescript-development:knip or python-development:python-dead-code). | [cleanup-auditor](<../../plugins/senior-review/roles/cleanup-auditor.md>) |
| Role | `senior-review:code-auditor` | Hunts coupling violations, broken abstractions, resource leaks, stale caches, and anti-patterns. TRIGGER WHEN: the user asks for a code review, architecture audit, quality scoring, failure-path analysis, or pattern consistency check. DO NOT TRIGGER WHEN: the task is security-specific auditing (use security-auditor). | [code-auditor](<../../plugins/senior-review/roles/code-auditor.md>) |
| Role | `senior-review:data-integrity-auditor` | Persistence-layer reviewer: impossible or inconsistent stored state. TRIGGER WHEN: the diff or target touches schemas, models, ORM entities, repositories, raw SQL, caches, or transaction boundaries; or the concern is partial writes, read-modify-write races, uniqueness enforced in code but not in the database, cache and database divergence, or eventual consistency consumed as strong. DO NOT TRIGGER WHEN: the concern is domain rules and state machines (use logic-integrity-auditor), migration mechanics (the data-migrations dimension), or cross-service message flows (use distributed-flow-auditor). | [data-integrity-auditor](<../../plugins/senior-review/roles/data-integrity-auditor.md>) |
| Role | `senior-review:distributed-flow-auditor` | Hunts cascading timeout violations, missing idempotency, broken saga compensation, message ordering bugs, and split-brain risks. TRIGGER WHEN: the target spans microservices, agent systems, or multiple modules and the question is cross-service: request flow tracing, contract mismatch between producer and consumer, or integration-boundary review. | [distributed-flow-auditor](<../../plugins/senior-review/roles/distributed-flow-auditor.md>) |
| Role | `senior-review:logic-integrity-auditor` | Cross-component reviewer for the guarantees recorded in `.team-review/02-interconnect.md`: ordering, idempotency, state machines, terminal states, domain rules, implicit assumptions. TRIGGER WHEN: /senior-review:team-review Phase 2 runs (always-on in the review preset), or the user asks for a logic, contract, or invariant audit. DO NOT TRIGGER WHEN: the task is surface-level style or lint review (use code-auditor), pure security auditing (use security-auditor), or the interconnect map does not exist yet (run semantic-interconnect-mapper first). | [logic-integrity-auditor](<../../plugins/senior-review/roles/logic-integrity-auditor.md>) |
| Role | `senior-review:premise-auditor` | Second, independent derivation of the code's claims, and attack on the load-bearing assumptions behind findings built from a common artifact. Two modes set by the spawning prompt: derivation blind to X-ray and the map, attack with both. TRIGGER WHEN: /senior-review:team-review Phase 1c runs, or the verification panel spawns Lens 0 for a finding whose premise_provenance is shared-context or mixed. DO NOT TRIGGER WHEN: the task is to find defects (use the dimension auditors), to build the interconnect map (use codebase-xray:semantic-interconnect-mapper), or to judge whether a defect is reachable (Lens 1). | [premise-auditor](<../../plugins/senior-review/roles/premise-auditor.md>) |
| Role | `senior-review:resource-lifecycle-auditor` | Reviewer for resource ownership and release on the success, error, and cancellation paths: leaks, double-release, use-after-release, unbounded pool growth. TRIGGER WHEN: the diff or target acquires file handles, sockets, streams, DB connections, subprocesses, event listeners, subscriptions, locks, threads, goroutines, timers, object URLs, or GPU and native memory; especially in C, C++, Rust, Go, or async code. DO NOT TRIGGER WHEN: the concern is behavior over time AFTER a leak (use temporal-resilience-auditor), memory-safety exploitation (use security-auditor), or general architecture (use code-auditor). | [resource-lifecycle-auditor](<../../plugins/senior-review/roles/resource-lifecycle-auditor.md>) |
| Role | `senior-review:security-auditor` | Attacker-mindset pass over the target: assumes it is exploitable and proves it. TRIGGER WHEN: the user asks for a security review, SAST audit, OWASP or CWE analysis, secret-leak scan, or an authentication or authorization code review; injection vectors, auth bypasses, crypto mistakes, or missing security headers. DO NOT TRIGGER WHEN: the concern is general code quality (use code-auditor) or infrastructure and network security (use platform-reviewer). | [security-auditor](<../../plugins/senior-review/roles/security-auditor.md>) |
| Role | `senior-review:temporal-resilience-auditor` | Reviewer for failure-over-time behavior: missing backoff or cap, errors swallowed until a subsystem dies silently, guards never cleared, notification floods and silence, clock hazards (suspend, DST, throttling). TRIGGER WHEN: the diff or target touches timers, schedulers, polling loops, retry and reconnect logic, queues, cron jobs, background workers, or watchdogs; or the pipeline flagged long-running execution. DO NOT TRIGGER WHEN: the concern is startup and bootstrap cycles (use chicken-egg-detector), cross-service timeout chains (use distributed-flow-auditor), or UI rendering races (use ui-race-auditor). | [temporal-resilience-auditor](<../../plugins/senior-review/roles/temporal-resilience-auditor.md>) |
| Role | `senior-review:ui-race-auditor` | Framework-agnostic UI timing analyst: React, Angular, Vue, Qt, GTK, Flutter, SwiftUI, Electron, Tauri. TRIGGER WHEN: races between async data loading, layout, event handlers, and programmatic scroll, focus, or resize; scroll position corruption, sticky or auto-scroll breakage, focus theft, layout shift, stale measurement closures, layout-dependent reads racing incomplete renders. | [ui-race-auditor](<../../plugins/senior-review/roles/ui-race-auditor.md>) |
| Workflow | `senior-review:code-review` | Auto-detects the scope, runs its analysis dimensions in parallel, and applies fixes with --fix or lands them with --commit. Reuses X-ray context when present. TRIGGER WHEN: the user asks for a code review, PR review, branch audit, or a security or architecture pass over recent changes; or asks to find and remove dead code, unused exports, unused dependencies, or orphan assets. For workspace tidying decided by the filesystem and git alone (committed build output, `.gitignore`, scratch directories, git state) use `/repo-hygiene:tidy`. DO NOT TRIGGER WHEN: a full multi-phase pipeline is wanted (use /senior-review:team-review) or a single file needs a style pass (use clean-code). | [code-review](<../../plugins/senior-review/workflows/code-review.md>) |
| Workflow | `senior-review:pr-review` | Generates a risk assessment, a review checklist, and a lite dead-code and VCS-hygiene pass over the diff, then submits it via gh with --create. TRIGGER WHEN: the user asks to prepare a PR, write a PR description, or open a pull request from the current branch. DO NOT TRIGGER WHEN: reviewing someone else's PR (use /senior-review:code-review with the PR number). | [pr-review](<../../plugins/senior-review/workflows/pr-review.md>) |
| Workflow | `senior-review:team-review` | Six-phase pipeline. Builds X-ray and interconnect context first, then runs specialized dimensions in parallel so cross-component logic bugs surface, not just local ones. TRIGGER WHEN: the user wants a multi-reviewer review of a whole codebase or a large change, or asks for the deepest review available. | [team-review](<../../plugins/senior-review/workflows/team-review.md>) |

### Workflow contracts

Contracts describe observable outputs; Markdown bodies define decisions,
flags, safety gates and execution. Declared `invoke` execution is unsupported.

#### `senior-review:code-review`

**Arguments:** <code>[PR number &#124; --branch &lt;name&gt; &#124; --commits N] [--fix] [--commit] [--auto-comment] [--strict] [--fast] [--rigorous]</code>

| Contract | Value |
|---|---|
| Inputs | `repository` |
| Outcomes | `code-review-completed` |
| Artifacts | `code-review-report` |
| Schemas | [project-protocol/contracts/work.toml](<../../plugins/project-protocol/contracts/work.toml>), [project-protocol/contracts/project-result.toml](<../../plugins/project-protocol/contracts/project-result.toml>) |
| Declared workers | `abstraction-architect/abstraction-architect-agent`, `platform-engineering/platform-reviewer`, `project-protocol/isolated-worker`, `react-development/react-performance-optimizer`, `senior-review/code-auditor`, `senior-review/data-integrity-auditor`, `senior-review/premise-auditor`, `senior-review/resource-lifecycle-auditor`, `senior-review/security-auditor`, `senior-review/temporal-resilience-auditor`, `senior-review/ui-race-auditor`, `testing/test-suite-auditor`, `typescript-development/type-safety-auditor` |
| Composed worker isolation | Required |
| Task-specific isolated workers | Allowed through the protocol role |
| Sidecar | [code-review.toml](<../../plugins/senior-review/workflows/code-review.toml>) |

| Phase | Needs | Dispatch | Isolation | Join | Concurrency |
|---|---|---|---|---|---|
| `run` | None | None | `shared` | None declared | `preferred` |

#### `senior-review:pr-review`

**Arguments:** `[--base main] [--create] [--split-check] [--strict-mode]`

| Contract | Value |
|---|---|
| Inputs | `repository` |
| Outcomes | `pr-review-completed` |
| Artifacts | `pr-review-report` |
| Schemas | [project-protocol/contracts/work.toml](<../../plugins/project-protocol/contracts/work.toml>), [project-protocol/contracts/project-result.toml](<../../plugins/project-protocol/contracts/project-result.toml>) |
| Declared workers | `platform-engineering/platform-reviewer`, `project-protocol/isolated-worker`, `react-development/react-performance-optimizer`, `senior-review/code-auditor`, `senior-review/premise-auditor`, `senior-review/security-auditor`, `typescript-development/type-safety-auditor` |
| Composed worker isolation | Required |
| Task-specific isolated workers | Allowed through the protocol role |
| Sidecar | [pr-review.toml](<../../plugins/senior-review/workflows/pr-review.toml>) |

| Phase | Needs | Dispatch | Isolation | Join | Concurrency |
|---|---|---|---|---|---|
| `run` | None | None | `shared` | None declared | `preferred` |

#### `senior-review:team-review`

**Arguments:** <code>&lt;target&gt; [--reviewers auto&#124;security,performance,react,typescript,platform,...] [--base-branch main] [--all] [--deep] [--no-context] [--fast] [--rigorous]</code>

| Contract | Value |
|---|---|
| Inputs | `repository`, `review-brief` |
| Outcomes | `reviewers-use-isolated-contexts`, `every-selected-dimension-is-dispatched-exactly-once`, `every-expected-reviewer-is-delivered-or-failed`, `consolidation-runs-only-after-the-delivery-barrier`, `cross-examination-runs-in-fresh-contexts`, `every-retained-finding-carries-evidence`, `only-the-consolidator-writes-the-final-report` |
| Artifacts | `final-report` |
| Schemas | [contracts/review-brief.toml](<../../plugins/senior-review/contracts/review-brief.toml>), [contracts/reviewer-binding.toml](<../../plugins/senior-review/contracts/reviewer-binding.toml>), [contracts/reviewer-selection.toml](<../../plugins/senior-review/contracts/reviewer-selection.toml>), [contracts/evidenced-finding.toml](<../../plugins/senior-review/contracts/evidenced-finding.toml>), [contracts/reviewer-result.toml](<../../plugins/senior-review/contracts/reviewer-result.toml>), [contracts/delivery-ledger.toml](<../../plugins/senior-review/contracts/delivery-ledger.toml>), [contracts/final-report.toml](<../../plugins/senior-review/contracts/final-report.toml>), [project-protocol/contracts/work.toml](<../../plugins/project-protocol/contracts/work.toml>), [project-protocol/contracts/project-result.toml](<../../plugins/project-protocol/contracts/project-result.toml>) |
| Declared workers | `abstraction-architect/abstraction-architect-agent`, `codebase-xray/semantic-interconnect-mapper`, `platform-engineering/platform-reviewer`, `project-protocol/isolated-worker`, `react-development/react-performance-optimizer`, `repo-hygiene/workspace-auditor`, `senior-review/api-contract-auditor`, `senior-review/chicken-egg-detector`, `senior-review/cleanup-auditor`, `senior-review/code-auditor`, `senior-review/data-integrity-auditor`, `senior-review/distributed-flow-auditor`, `senior-review/logic-integrity-auditor`, `senior-review/premise-auditor`, `senior-review/resource-lifecycle-auditor`, `senior-review/security-auditor`, `senior-review/temporal-resilience-auditor`, `senior-review/ui-race-auditor`, `testing/test-suite-auditor`, `typescript-development/type-safety-auditor` |
| Composed worker isolation | Required |
| Task-specific isolated workers | Allowed through the protocol role |
| Sidecar | [team-review.toml](<../../plugins/senior-review/workflows/team-review.toml>) |

| Phase | Needs | Dispatch | Isolation | Join | Concurrency |
|---|---|---|---|---|---|
| `scope` | None | None | `shared` | None declared | `preferred` |
| `context-building` | `scope` | None | `shared` | None declared | `preferred` |
| `dimension-detection` | `context-building` | None | `shared` | None declared | `preferred` |
| `independent-review` | `dimension-detection` | `per item in selection:reviewers` | `required` | `all-delivered` | `preferred` |
| `delivery-accounting` | `independent-review` | None | `shared` | None declared | `preferred` |
| `initial-consolidation` | `delivery-accounting` | None | `shared` | None declared | `preferred` |
| `cross-examination` | `initial-consolidation` | `role:premise-auditor`, `role:logic-integrity-auditor` | `required` | `all-delivered` | `preferred` |
| `consolidation` | `cross-examination` | `code-auditor` | `required` | None declared | `preferred` |
| `report-delivery` | `consolidation` | None | `shared` | None declared | `preferred` |

### Host exports

Package paths and coordination are derived from the host adapters. `native`
and `adapted` describe bindings, not successful installed-host execution.

The selected strategy is an adapter binding even for a flat workflow body.
A dispatch harness is rendered only for declared method workers, task-specific
workers or phase fan-out; the host reference explains the entry artifacts.

| Host | Package | Binding | Selected workflow strategy |
|---|---|---|---|
| claude | [exports/claude/plugins/senior-review](<../../exports/claude/plugins/senior-review>) | `native` | `code-review: native-team`, `pr-review: native-team`, `team-review: native-team` |
| copilot | [exports/copilot/plugins/senior-review](<../../exports/copilot/plugins/senior-review>) | `native` | `code-review: parallel-subagents`, `pr-review: parallel-subagents`, `team-review: parallel-subagents` |
| codex | [exports/codex/plugins/senior-review](<../../exports/codex/plugins/senior-review>) | `adapted` | `code-review: parallel-subagents`, `pr-review: parallel-subagents`, `team-review: parallel-subagents` |
| pi | [exports/pi/plugins/senior-review](<../../exports/pi/plugins/senior-review>) | `adapted` | `code-review: parallel-subagents`, `pr-review: parallel-subagents`, `team-review: parallel-subagents` |
| opencode | [exports/opencode/plugins/senior-review](<../../exports/opencode/plugins/senior-review>) | `native` | `code-review: parallel-subagents`, `pr-review: parallel-subagents`, `team-review: parallel-subagents` |

<!-- daodan:reference:end -->
