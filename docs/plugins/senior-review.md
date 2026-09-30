# Senior Review Plugin

> Catch bugs before they ship. Twelve specialized agents: eleven review code quality, security, UI timing, distributed flows, startup cycles, temporal resilience (failure-over-time), data integrity (persistence semantics), resource lifecycle (ownership and release), cross-component logic integrity, formal API contracts, and codebase hygiene in parallel, and the twelfth, `premise-auditor`, derives the code's claims a second time, independently, and attacks the premises findings stand on. The reviewers read a shared contract/invariant map built by `codebase-xray:semantic-interconnect-mapper`, which is why they find bugs that are invisible from local-only inspection. Backed by a comprehensive defect taxonomy knowledge base with 140+ defect patterns and CWE/OWASP mappings. `/senior-review:team-review` runs all of it as a single pipeline, with an adversarial verification panel and a completeness critic as quality gates before the report ships.

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

Quality gates for multi-reviewer code review pipelines: the context-sharing pattern that lets reviewers cite a shared interconnect map instead of re-reading code from scratch, the adversarial verification panel that re-judges every consolidated finding, the completeness critic that reports what the review failed to cover, evidence classes for quantitative claims, and the delivery gate. Consumed by `/senior-review:team-review` (Phases 1, 3, 4b, 4c, 5) and `/senior-review:code-review` (Steps 4b/4c). Since 8.0.0 the skill also carries three `references/` files (`code-review-agents.md`, `code-review-fix-loop.md`, `code-review-output.md`) that hold the full agent prompts, fix-loop workflow, and output templates of `/senior-review:code-review`, loaded on demand so the command itself stays thin (about 350-400 lines).

**Shared-Context Provenance Rule:** the skill's first-level invariant, and the reason the rest of this section reads the way it does. Evidence derived from a shared artifact cannot independently corroborate the claims in that same artifact: N reviewers agreeing on a premise they were all handed is one observation, not N. Three consequences bind every gate: a reviewer that consumed a claim has not verified it, agreement across a shared premise is an **echo** that raises neither confidence nor severity, and no metric may reward agreement with a shared artifact.

**Context Sharing Pattern:** reviewers read the X-ray run directory plus `.team-review/02-interconnect.md` (contracts, invariants, domain rules, assumptions, integration hot-spots) and `.team-review/01-knowledge-provenance.md`, guided by anchor routing per dimension (security reads Integration Hot-Spots plus unverified Assumptions; logic-integrity reads Contracts, Invariants, and Domain Rules; and so on). Every finding declares two extra fields: its **load-bearing premise** (the single proposition whose falsity collapses it) and that premise's **provenance** (`independent`, `shared-context`, or `mixed`, recording causal dependence rather than citation). The **map utilization rate** (share of findings citing a map anchor) is an operational number only, and no target is set for it: a high value on a wrong map is the signature of the failure this pipeline exists to prevent. The quality signals are elsewhere: independent premise reconstruction rate, premise challenge rate, map challenge rate, map gap rate, and cross-source corroboration.

**Adversarial Verification Panel:** every finding above a 50% confidence floor is judged by up to 4 lenses (Premise Challenge, Reachability/Correctness, False-Positive Causes, Severity Calibration). **Lens 0 is a veto, gated and first.** It runs on findings whose premise provenance is `shared-context` or `mixed`, and on any finding whose declared premise carries a universal or negative quantifier (`no`, `never`, `cannot`, `always`, `only`) at any provenance, since an over-scoped premise can be born independently as easily as it can be inherited. It attacks the premise rather than the finding and returns `REFUTED` only with a `file:line` counterexample, stating whether that counterexample kills the PREMISE itself or only a piece of shared SUPPORT: killing the premise discards the finding as `filtered: premise-refuted` without spending lenses 1-2, while `UNCERTAIN` proceeds tagged `premise-contested`. It never kills a finding by failing, since error, malformed output and evidence-free refutation all collapse to `UNCERTAIN`. Lenses 1-2 then run in parallel; lens 3 is **gated on survival** (calibrating a finding about to be discarded is spend for nothing, and the gate cuts roughly a third of verifier calls). A finding survives if at least 2 of lenses 1-2 vote REAL, is discarded (`filtered`) if at least 2 vote FALSE_POSITIVE, and survives `contested` on a tie. Final severity comes from lens 3's vote. A cost guard (a finding-count proxy, not a token budget) narrows verification to Critical/High plus an uncertainty band once more than 25 findings survive dedup, unless `--rigorous` is passed; `--fast` skips the panel entirely.

**Evidence Classes:** any finding that quantifies damage labels the number `measured` (harness, simulation, logs, with the method stated) or `derived` (computed by reading the code). A `derived` number alone cannot justify Critical severity, and no finding can be closed as acceptable ("bounded", "low traffic") without also answering the **user-visible-consequence question**: what does the user see, and when? "Nothing, silently" escalates severity rather than closing the finding.

**Delivery Gate:** consolidation does not start until every spawned reviewer has delivered its findings file or an explicit no-findings report; a silent reviewer is nudged once, then salvaged and reported as **degraded**, never presented as clean. Before the report is finalized, the post-review `git status --porcelain` is diffed against the pre-review snapshot and anything the review created outside its session directory (probe scripts, measurement harnesses) is removed and noted.

**Completeness Critic:** one agent checks coverage against a fixed gap taxonomy (dimensions warranted but not run, in-scope files cited by no finding, unverified interconnect assumptions untouched by any finding, high-risk hot-spots with zero findings, and findings closed on a metric alone without a stated user-visible consequence) and may trigger one bounded follow-up round for the single highest-risk gap it names.

**Reviewer Pipeline Conventions:** every Phase 2 reviewer carries a scope budget (stops after ~15 file reads without a finding), a no-findings protocol (a clean "examined X, Y, Z: no issues" report is valid, not a failure), and a `## Cross-Reviewer Notes` section for observations that belong to another dimension.

---

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
| 5. Report & cleanup | Workspace hygiene check against the pre-review `git status` snapshot, then the consolidated report with the map-utilization number, the premise metrics, and the corroborated-versus-echo counts; `.team-review/` is preserved for later reference |

**Always-on dimensions:** security, architecture, logic integrity (skipped under `--no-context`), codebase hygiene (`cleanup-auditor`), workspace hygiene (`repo-hygiene:workspace-auditor`: filesystem garbage, generated artifacts tracked in VCS, `.gitignore` completeness, scratch and pipeline-output directories, orphan doc-assets, git auxiliary state; disjoint from codebase hygiene by construction).

**Conditional dimensions** (auto-detected): UI races, distributed flows, circular dependencies, temporal resilience (`temporal-resilience-auditor`, activated by timers, schedulers, retry/reconnect, polling, cron, and daemon signals in the diff), data integrity (`data-integrity-auditor`, activated by schema, ORM, raw SQL, cache, and transaction signals), resource lifecycle (`resource-lifecycle-auditor`, activated by file/socket/connection/subprocess/listener/lock/task acquisition signals), and API contracts (`api-contract-auditor`, activated by a formal contract file such as `*.proto`, `openapi*.y*ml`, `*.graphql`, or `asyncapi*`, as well as by route and serializer changes) all resolve to specialized agents in this plugin. React performance, platform / runtime integration, structural entropy (`abstraction-architect:abstraction-architect` in diff mode, activated only when the target is a diff that adds code), and TypeScript type safety (dimension `ts-safety` in team-review, Agent K in code-review; `typescript-development:type-safety-auditor`, activated when changed files match `\.tsx?$` and `tsconfig.json` exists) resolve to agents in `react-development`, `platform-engineering`, `abstraction-architect`, and `typescript-development`, which are hard dependencies, so the marketplace installs them with `senior-review` and a dimension is skipped only when the change shows no signal for it. `logic-integrity-auditor` findings that violate a rule the interconnect map never surfaced carry the `[MAP-GAP]` marker and are also reported as mapper coverage gaps. Testing quality resolves to `testing:test-suite-auditor`, which is a hard dependency like the others, so the dimension runs whenever the change touches test files. General performance (activated by frontend files with no React dependency) resolves to `senior-review:code-auditor`, and data migrations (activated by migration files) to `senior-review:data-integrity-auditor`. There is no generic fallback: if a spawn fails with "Agent type not found", the install is broken and the command stops and reports it.

```
/senior-review:team-review src/auth/                                # auto-detected dimensions
/senior-review:team-review main...HEAD --reviewers security,testing # explicit dimensions on a diff
/senior-review:team-review #42 --rigorous                           # PR review, verify every finding
/senior-review:team-review src/ --no-context                        # raw mode, no context phase
```

`--no-context` reproduces the pre-pipeline behavior: no context phase, no `logic-integrity-auditor`, reviewers see only the target and diff. Use it for quick scans or targets under roughly 100 LOC.

---

### `/senior-review:code-review`

Unified code review that auto-detects scope: uncommitted/staged changes, recent commits, PR number, or branch diff. Dispatches up to 15 agents in parallel (A, B, B2, then C through N): always-on code audit (A), security (B), lite dead-code and VCS hygiene scoped to the diff (B2), and git history (E), plus conditional UI races, platform / runtime integration, testing, API contracts, data migrations, React performance, structural entropy, TypeScript type safety, temporal resilience, data integrity, and resource lifecycle. The command holds the dispatch table and conditions; the full agent prompts, fix-loop workflow, and output templates load on demand from the `review-quality-gates` skill's `references/` files (progressive disclosure, since 8.0.0).

Agent J is the structural-entropy review, `abstraction-architect:abstraction-architect`. It runs whenever the diff adds code (at least one function, method, class, module, constant table, or block longer than roughly five lines) and is skipped only for diffs that are purely deletions, renames, formatting, or config edits. It is the one agent whose question is about the rest of the codebase: it takes the diff as an anchor and asks whether the diff adds a second place where a concept the codebase already owns now lives. It covers seven dimensions over two evidence tracks. The knowledge track (duplicated domain knowledge, competing sources of truth, redundant representation, duplicated or derivable state) is judged by semantic identity and ownership, seeded by `.abstraction-architect/concept-index.json` when one exists; without it the agent works from diff-anchored discovery and says so. The form track (missed unification, prior art available, abstraction fitness) is judged by recurrence, and the Rule of Three applies only to missed unification. `code-auditor` keeps the single-file abstraction smells.

**Invoke:** `/senior-review:code-review [PR number | --branch <name> | --commits N] [--fix] [--commit] [--auto-comment] [--strict] [--fast] [--rigorous]`. `--strict` makes any Critical finding force a `Not ready` verdict; `--fast` skips the verification panel and the completeness critic; `--rigorous` verifies every finding above the confidence floor, ignoring the cost guard.

**Fix flags (8.0.0, breaking):** `--fix` applies the fixes and verifies (build+test) but commits nothing, leaving the working tree for the user to review. `--commit` implies `--fix` and adds the commits: one per fix or batch in Step 7b, one per phase in Step 7c. The Step 7c bulk cleanup runs only under `--commit`, because its per-phase commits are its revert mechanism.

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
| **Removal** | `/senior-review:code-review --commit` Step 7c | Five phases lowest-risk-first (`brand`, `assets`, `deps`, `exports`, `docs`), one commit each, build and test gate between phases, `git reset --hard HEAD~1` on failure |

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
