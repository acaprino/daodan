

## Existing analysis compatibility

Coordinators load `codebase-map:map-method` and apply `references/migration.md`
before root lookup or dispatch. Workers never migrate roots: use only its
`migrate_root.py resolve` for supplied bindings. Propagate returned paths.
Failed migration/resolution or a still-legacy `.codebase-xray` path blocks the
dependent operation; preserve archives and run IDs.

## Execution requirements

This workflow fans out over the dimensions its detection step selects. Dispatch, scheduling and result
collection belong to the host harness, generated from `contracts/team-review.workflow.toml`. What this
workflow requires of any harness is fixed, and none of it is optional:

- every reviewer runs in its own context and never reads another reviewer's result
- exactly the selected dimensions are dispatched, once each
- every expected reviewer is recorded `delivered` or `failed` before anything is consolidated
- cross-examination runs after that barrier, in fresh contexts
- only the consolidation phase writes the final report

If the host cannot run reviewers in isolated contexts, stop and say so. A review whose dimensions
shared a context is not the artifact this workflow claims to produce.

# Team Review (Pipeline)

| Phase | Work | Output |
|---|---|---|
| 0 | Resolve the target (0), detect dimensions (0b), discover the evidence this review needs without reading any Codebase Map output (0c) | `.team-review/00-scope.md`, `01a-review-knowledge-leads.md` |
| 1 | Codebase Map analysis (1a) and blind premise derivation (1c) in parallel, joined (1d), then the interconnect map (1b) | `01b-independent-claims.md`, `01-knowledge-provenance.md`, `02-interconnect.md` |
| 2 | One isolated reviewer per selected dimension; every finding declares its load-bearing premise and its provenance | `findings-<dim>.md` |
| 3 | Delivery barrier: every reviewer delivers findings or an explicit no-findings report | ledger |
| 4 | Consolidation weighted by provenance, verification panel (4b), completeness critic (4c) | `99-consolidated.md` |
| 5 | Report and cleanup | final report |

**Raw mode**: `--no-context` runs reviewers on the target and diff only: no Phase 0c, no Phase 1, no `logic-integrity-auditor`, no `premise-auditor` in either mode.

## Skills to Load

Before starting, invoke these skills to inform the review process:
- `senior-review:review-quality-gates`: provenance rule and reviewer conventions in its core; its `references/context-sharing.md` for anchor routing before dispatch
- `senior-review:defect-taxonomy`: 140+ defect subcategories with CWE/OWASP mappings (includes `logic-integrity.md`)

## Pre-flight Checks

1. Confirm the harness can dispatch isolated reviewers; stop if it cannot.
2. Parse `$ARGUMENTS`:
   - `<target>`: file path, directory, git diff range (e.g., `main...HEAD`), or PR number (e.g., `#123`)
   - `--reviewers`: comma-separated dimensions OR `auto` (default: `auto`)
   - `--base-branch`: base branch for diff comparison (default: `main`)
   - `--all`: force all dimensions regardless of auto-detection
   - `--deep`: run Phase 1a `codebase-map` in full mode (default: `--depth=lite`)
   - `--no-context`: skip Phase 0c and Phase 1 entirely and run reviewers with raw code only (raw mode; `logic-integrity-auditor` and `premise-auditor` are also skipped)
   - `--fast`: skip the verification + completeness-critic gate entirely (Phase 4b and 4c)
   - `--rigorous`: verify every finding above the confidence floor, ignoring the cost-guard cap
3. Check for existing `.team-review/state.json`:
   - If present with `status: "in_progress"`: ask user whether to resume or start fresh (archive to `.team-review-<ISO-timestamp>/`).
   - If present with `status: "complete"`: ask whether to archive and start fresh.
   - If absent: proceed to new session.
4. Initialize `.team-review/` with `state.json`:

   ```json
   {
     "target": "$ARGUMENTS",
     "status": "in_progress",
     "flags": {
       "reviewers": "auto",
       "all": false,
       "deep": false,
       "no_context": false,
       "fast": false,
       "rigorous": false
     },
     "current_phase": 0,
     "phases": {
       "phase_0_resolution": "pending",
       "phase_0b_detection": "pending",
       "phase_0c_evidence_discovery": "pending",
       "phase_1c_premise_audit": "pending",
       "phase_1d_reconciliation": "pending",
       "phase_1a_xray": "pending",
       "phase_1b_interconnect": "pending",
       "phase_2_review": "pending",
       "phase_3_consolidation": "pending",
       "phase_4b_verification": "pending",
       "phase_4c_critic": "pending",
       "phase_4_report": "pending"
     },
     "files_created": [],
     "xray": {
       "run_id": null,
       "run_dir": null,
       "target": null,
       "depth": null
     },
     "started_at": "ISO_TIMESTAMP"
   }
   ```

## Phase 0: Target Resolution

1. Determine target type, after `references/candidate-grounding.md` has fixed the target kind:
   - **File/Directory**: use as-is for review scope
   - **Git diff range**: `git diff {range} --name-only` to get changed files
   - **PR number**: `gh pr diff {number} --name-only` to get changed files
   - **Plan, specification or document**: the paths, symbols and contracts it names, resolved against the current tree, are the review scope; the file itself is the artifact under review
2. Collect the full diff content for later distribution to reviewers.
3. Collect the list of changed file paths and extensions for Phase 0b.
4. Write `.team-review/00-scope.md` with target, files, flags. Append a `## Pre-review work tree` section containing the output of `git status --porcelain` at this moment: the Phase 5 workspace hygiene check diffs against it. Mark phase complete in `state.json`.

## Phase 0b: Context Detection (when `--reviewers auto` or omitted)

Analyze changed files and codebase to determine which review dimensions are relevant. Skip if explicit `--reviewers` list was provided.

Include the stack dimensions from `references/stack-dimensions.md` inside this
skill in the same selection. That reference also defines explicit reviewer scope
and --all behavior. Present their activation evidence or skip/gap reasons with
the other dimensions before dispatch.

### Always-on dimensions (run for every review)

| Dimension | Agent | Rationale |
|-----------|-------|-----------|
| Security | `senior-review:security-auditor` | Every change can introduce vulnerabilities |
| Architecture | `senior-review:code-auditor` | Coupling, abstractions, failure flows, pattern consistency, scoring |
| **Logic integrity** | `senior-review:logic-integrity-auditor` | **Hunts violations of contracts/invariants/domain rules surfaced in Phase 1b** (skipped if `--no-context`) |
| Codebase hygiene | `senior-review:cleanup-auditor` | The **full** pass across all five dimensions that need source comprehension, over the whole codebase: dead code, orphan assets, phantom/unused deps plus barrel-file and eager-bundle bloat, stale documentation, and lifecycle archaeology. `/senior-review:code-review` and `/senior-review:pr-review` run only the lite subset (dead code, scoped to the diff), so this dimension is where the other four get covered at all |
| Workspace hygiene | `repo-hygiene:workspace-auditor` | Everything the filesystem and git decide without reading a symbol: filesystem garbage, generated artifacts tracked in VCS, `.gitignore` completeness and archaeology, scratch and pipeline-output directories, orphan doc-assets, git auxiliary state. Disjoint from the row above by construction, so the two never contest the same finding |

### Conditional dimensions (auto-detected from context)

Run these checks against the changed files and codebase to decide which extra reviewers to spawn.

Structural entropy and testing quality live in required plugins `abstraction-architect` and `testing`. Workspace hygiene comes from required `repo-hygiene`. Skip a dimension only when its code signal does not match; failed dispatch must be reported as degraded delivery.

| Signal | Detection rule | Dimension activated | Agent |
|--------|---------------|---------------------|-------|
| **UI/frontend files** | Changed files include `.tsx`, `.jsx`, `.vue`, `.svelte`, `.component.ts`, or files containing scroll/focus/layout manipulation | UI race conditions | `senior-review:ui-race-auditor` |
| **Non-React frontend** | Frontend files detected but no React dependency | General performance | `senior-review:code-auditor` (performance dimension) |
| **Multi-service / messaging** | Changed files touch API routes, message handlers, gRPC definitions, queue consumers/producers, or `docker-compose.yml` with multiple services | Distributed flows | `senior-review:distributed-flow-auditor` |
| **Init/startup code** | Changed files touch startup sequences, dependency injection, config bootstrap, migration runners, or service registration | Circular dependencies | `senior-review:chicken-egg-detector` |
| **Long-running / scheduled execution** | Diff or changed files touch timers, schedulers, polling loops, retry/reconnect logic, cron jobs, queue workers, background daemons, updaters, or watchdogs (see detection command 5b) | Temporal resilience (**what does the user see after this has been failing for a day?**) | `senior-review:temporal-resilience-auditor` |
| **Persistence code** | Diff or changed files touch schemas, models, ORM entities, repositories, raw SQL, cache layers, or transaction boundaries (see detection command 5c) | Data integrity (**can the store be made to hold an impossible state?**) | `senior-review:data-integrity-auditor` |
| **Resource acquisition** | Diff or changed files acquire files, sockets, connections, subprocesses, listeners, subscriptions, locks, tasks, or timers, especially in manual-resource languages (C/C++/Rust/Go) or async-heavy code (see detection command 5d) | Resource lifecycle (**does every acquire release on success, error, AND cancellation?**) | `senior-review:resource-lifecycle-auditor` |
| **Test files** | Changed files match `test_*`, `*_test.*`, `*.spec.*`, `*.test.*`, `conftest.py`, `__tests__/` | Testing quality | `testing:test-suite-auditor` |
| **API files** | Changed files touch a formal contract file (`*.proto`, `openapi*.y*ml`, `swagger*`, `*.graphql`, `asyncapi*`, JSON Schema), or route definitions, serializers, or DTO/model declarations | API contracts | `senior-review:api-contract-auditor` |
| **Migration files** | Changed files match database migration patterns (Alembic, Django, Rails, Prisma, SQL migrations) | Data migrations | `senior-review:data-integrity-auditor` (migration dimension) |
| **Diff target adding code** | Target resolved to a diff in Phase 0 (git range, PR number, or uncommitted changes) AND the diff adds at least one function, method, class, module, constant table, or block longer than roughly five lines. Never activated for plain file/directory targets: there is no diff to anchor on, and the whole-tree question belongs to `/abstraction-architect:audit` | Structural entropy (**does this diff add a second place where a concept the codebase already owns lives?** Seven dimensions over two evidence tracks, diff-anchored: duplicated domain knowledge, competing sources of truth, redundant representation, duplicated or derivable state, missed unification, prior art available, abstraction fitness) | `abstraction-architect:abstraction-architect-agent` (mode `diff`) |

### Detection implementation

Run these bash commands to gather signals:

```bash
# 1. Classify changed file extensions
echo "$CHANGED_FILES" | sed 's/.*\.//' | sort | uniq -c | sort -rn

# 4. Check for multi-service / messaging patterns in diff
echo "$DIFF_CONTENT" | grep -qiE 'rabbitmq\|amqp\|kafka\|grpc\|pubsub\|queue\|celery\|dramatiq' && echo "MESSAGING=true"
echo "$CHANGED_FILES" | grep -qiE 'routes?\b|api/|endpoints?/|handlers?/' && echo "API_FILES=true"
# Formal contract files. Kept separate from API_FILES on purpose: a change to
# openapi.yaml or schema.graphql matches none of the path patterns above, and
# it is the single strongest signal for the api-contract-auditor dimension.
echo "$CHANGED_FILES" | grep -qiE '\.proto$|\.graphql$|\.gql$|openapi.*\.(ya?ml|json)$|swagger.*\.(ya?ml|json)$|asyncapi.*\.(ya?ml|json)$|schema.*\.json$' && echo "CONTRACT_FILES=true"

# 5. Check for init/startup patterns in diff
echo "$DIFF_CONTENT" | grep -qiE 'def main\b|if __name__|app\.on_startup|@app\.on_event|lifespan|create_app|bootstrap|init_' && echo "STARTUP=true"

# 5b. Check for long-running / scheduled execution patterns (temporal resilience)
echo "$DIFF_CONTENT" | grep -qiE 'setInterval|setTimeout|cron|schedule|\bretry|reconnect|backoff|watchdog|heartbeat|keepalive|\bpoll(ing)?\b|background.?(task|worker|job)|daemon|updater' && echo "TEMPORAL=true"

# 5c. Check for persistence code (data integrity)
echo "$DIFF_CONTENT" | grep -qiE '\btransaction\b|\bcommit\b|rollback|UPDATE |INSERT |upsert|\bunique\b|constraint|ON CONFLICT|FOR UPDATE|select_for_update|session\.add|\.objects\.|prisma\.|typeorm|sqlalchemy|redis|cache\.(get|set|del)' && echo "PERSISTENCE=true"

# 5d. Check for resource acquisition (resource lifecycle)
echo "$DIFF_CONTENT" | grep -qiE 'open\(|createReadStream|createWriteStream|\bsocket\b|getConnection|acquire|addEventListener|subscribe\(|\block\b|mutex|semaphore|new Worker|subprocess|Popen|spawn\(|go func|tokio::spawn|asyncio\.create_task|createObjectURL' && echo "RESOURCES=true"

# 6. Check for test and migration files
echo "$CHANGED_FILES" | grep -qiE 'test_|_test\.|\.spec\.|\.test\.|conftest|__tests__' && echo "TEST_FILES=true"
echo "$CHANGED_FILES" | grep -qiE 'migrat|alembic|versions/' && echo "MIGRATION_FILES=true"
```

### Display detected dimensions

After detection, display the plan:

```
Context detection complete:
  - Always: security, architecture, logic-integrity, codebase-hygiene, workspace-hygiene
  - Detected: ui-races (6 .tsx files), distributed-flows (API routes + RabbitMQ), temporal-resilience (retry + scheduler code), data-integrity (ORM writes + transactions), abstraction (diff adds 4 units)
  - Skipped: chicken-egg (no startup code)

Pipeline plan:
  Phase 0c: review evidence discovery (inline)
  Phase 1a: codebase-map (--depth=lite)   |  Phase 1c: premise-auditor (parallel, blind)
  Phase 1d: knowledge reconciliation (inline)
  Phase 1b: codebase-map:semantic-interconnect-mapper
  Phase 2:  {N} reviewers in parallel
  Phase 3:  monitor and collect (delivery barrier)
  Phase 4:  consolidation, verification (4b), completeness critic (4c)
  Phase 5:  report
```

Every reason on the Skipped line is a statement about the code, never about the install: "no startup code" means the code did not need the dimension. Every agent this command can spawn comes from a plugin `senior-review` declares as a hard dependency, so there is no "plugin not installed" reason and no generic fallback. If a spawn fails with "Agent type not found", stop and report the broken install instead of continuing with a silently reduced review.

Mark `phase_0b_detection` complete in `state.json`.

## Phase 0c: Review Evidence Discovery

Runs inline in the orchestrating context on every invocation except raw mode. It discovers what evidence is relevant to this review; how the repository documents itself is the Codebase Map's discovery. **It never reads `.codebase-map/` in any form**, the mirror and earlier runs included: the Codebase Map's leads enter at the Phase 1d join and nowhere earlier.

1. Read `CLAUDE.md`, `AGENTS.md` and equivalent project instruction files, and follow any navigation rule they state. If the project says a specific file is where to look first to find where a concept lives, open that file before opening any code. Discover the conventions from the repository itself, never from a prior Codebase Map run.
2. Extract the concepts, domains and symbols the diff touches. Names of changed functions, classes, modules and config keys are the starting set; add the domain nouns that appear in the diff's own strings and comments.
3. For each concept, search the project's indexes and documentation for a relevant entry, and search the tests for behaviour that encodes it.
4. Write `.team-review/01a-review-knowledge-leads.md`.

**This file is immutable once written.** No later phase appends to it. Codebase Map's own leads are joined into a separate derived artifact in Phase 1d, precisely so that the snapshot Phase 1c consumes cannot change underneath it.

**Output:** `.team-review/01a-review-knowledge-leads.md`

```markdown
# Review Knowledge Leads

> Leads, not truth. Immutable once written.
> Discovered by senior-review independently of any Codebase Map output.

## Navigation rules followed
| Source | Rule |
|--------|------|

## Concepts touched by this diff
| Concept | Where it appears in the diff |
|---------|------------------------------|

## Leads
| Concept | Document / test | Anchor | Status |
|---------|-----------------|--------|--------|

## Concepts with no lead found
[One line each. This list is the honest statement of what nobody documented.]
```

Mark `phase_0c_evidence_discovery` complete in `state.json`.

## Phase 1: Context Building

The sub-phases below are listed in **execution order**, not in label order: 1a and 1c start together, 1d joins them, 1b runs last on the joined result. Nothing named here is missing.

Skip this phase entirely if `--no-context` was passed. Mark `phase_1a_xray`, `phase_1c_premise_audit`, `phase_1d_reconciliation`, `phase_1b_interconnect`, and `phase_0c_evidence_discovery` as `skipped` in `state.json`. Jump to Phase 2 with raw target files only.

### Phase 1a: Codebase Map Analysis

The review coordinator executes the `codebase-map:analyze` entry's preflight, checkpoints, delivery check and publication decision, and dispatches `codebase-map:map-analyst` in one isolated context for the phases. Loading a method or role body runs nothing. Phase 1c, Phase 1b and every reviewer keep their own isolated contexts.

1. Execute the `codebase-map:analyze` preflight and coordinator-owned delivery/publication steps against the target. Dispatch `codebase-map:map-analyst` in an isolated context for its requested phases, preserving the canonical scope checkpoints, run binding, output and completion gates:
   - Default mode: `--depth=lite` (structure + interfaces + risks only)
   - If `--deep` flag: full analysis
   - Target scope: the files from Phase 0
2. Read `.codebase-map/runs.json` to resolve the run the workflow just created, and record it in `state.json -> xray` as `run_id`, `run_dir`, `target` and `depth`. Every later phase derives its paths from this block and never from the `.codebase-map/` root. `$XRAY_RUN_DIR` below always means `state.json -> xray.run_dir`. If the run cannot be resolved, halt: an unresolvable provenance is a broken pipeline, not a reason to fall back to the mirror.
3. Verify on completion that at minimum `01-structure.md`, `02-interfaces.md`, and `05-risks.md` exist.
4. Mark `phase_1a_xray` complete.

If the analysis fails or produces no output, halt the pipeline and report a broken installation. Never substitute another worker for the analyst: Phase 1b and Phase 2 depend on the file names and section anchors the analysis itself produces.

### Phase 1c: Independent Premise Derivation (parallel with 1a)

Dispatch when Phase 1a starts, without waiting for it: this derivation must not see what the Codebase Map derived.

1. Dispatch the `senior-review:premise-auditor` agent in its own isolated context.
2. Prompt:

   ```
   Mode 1: independent derivation.

   Target scope: [contents of .team-review/00-scope.md]
   Knowledge leads: .team-review/01a-review-knowledge-leads.md
   Diff: {diff content}

   Derive independently what is true about the concepts this diff touches.
   Write .team-review/01b-independent-claims.md in the format your agent
   definition prescribes.

   You have NO access to .codebase-map/ or to .team-review/02-interconnect.md.
   Neither exists for you. Do not look for them, and report contamination if
   anything in this prompt paraphrases a Codebase Map conclusion.
   ```

3. Wait for both 1a and 1c before starting Phase 1d. Mark `phase_1c_premise_audit` complete.

Under raw mode (`--no-context`) this phase does not run, because there is no shared derivation for it to be independent of.

### Phase 1d: Knowledge Reconciliation (join)

Runs inline once both 1a and 1c have completed. The premise auditor never compares its own derivation; this join does.

Read `.team-review/01a-review-knowledge-leads.md`, `$XRAY_RUN_DIR/knowledge/documentation-leads.md` and `.team-review/01b-independent-claims.md`. Write:

**Degradation when Codebase Map produced no leads.** If `$XRAY_RUN_DIR/knowledge/documentation-leads.md` does not exist, record `Inherited from Codebase Map: not produced` under that heading and **suppress the asymmetry diagnostic** described below for this run. An absent file is not a discovery gap, and treating it as one would report a Codebase Map gap on every row: a systematically false signal from the mechanism built to stop false signals. A reused older run, a Phase 0 that failed, and a Codebase Map version predating Phase 0 all land here. Everything else in this phase proceeds normally: `Missing` and `Disputed` are still computed from `01a` and `01b`.

**Output:** `.team-review/01-knowledge-provenance.md`

```markdown
# Knowledge Provenance

> Derived view, produced after both discovery branches completed.
> The canonical artifact consumed downstream. 01a and 01b are its sources.

## Independently discovered by Senior Review
[rows from 01a-review-knowledge-leads.md]

## Inherited from Codebase Map
[rows from $XRAY_RUN_DIR/knowledge/documentation-leads.md]

## Missing
| Concept | In scope because |
|---------|------------------|
| [concept] | [where it appears in the diff] |

## Disputed
| Claim | Independent derivation says | Codebase Map says |
|-------|------------------------------|------------|
| [claim] | [X at file:line] | [Y at file:line] |
```

**Missing and Disputed never collapse into one section.**

| Section | Maps to in the interconnect map | Never |
|---|---|---|
| `Missing` | a coverage gap, and `unverified` on any related row | `disputed`: nobody finding documentation is not two sources disagreeing |
| `Disputed` | `disputed`, both `file:line` sides cited | silently resolved in favour of either derivation |

A concept `01a` carried and the Codebase Map's leads missed stays under `Independently discovered by Senior Review`; a concept neither found goes to `Missing`; neither is downgraded because the other branch was silent. Record both asymmetries as diagnostics: a row only in the independent section is a Codebase Map discovery gap, a row only in the inherited section is a Phase 0c gap. Neither is reported when the Codebase Map produced no leads file.

Mark `phase_1d_reconciliation` complete.

### Phase 1b: Semantic Interconnect Mapping

1. Dispatch the `codebase-map:semantic-interconnect-mapper` agent in its own isolated context.
2. Prompt:

   ```
   Build the interconnect map for this review.

   Target scope: [contents of .team-review/00-scope.md]
   Codebase Map output: $XRAY_RUN_DIR (files: 01-structure.md, 02-interfaces.md, 05-risks.md, knowledge/documentation-leads.md, ...)
   Independent claims: .team-review/01b-independent-claims.md
   Knowledge provenance: .team-review/01-knowledge-provenance.md

   Read $XRAY_RUN_DIR and the target files. Produce .team-review/02-interconnect.md
   following the exact output format in your agent definition (Call Graph,
   Contracts formal/structural/implicit, Invariants, Domain Rules, Assumptions,
   Integration Hot-Spots, Change Impact Radius, Reviewer Hints).

   Every claim must cite file:line. No recommendations, no fixes.

   Compare the independent claims against your own derivation. Every
   contradiction becomes a `disputed` row citing both sides. Do not resolve
   contradictions and do not prefer your own derivation by default.
   ```

3. Wait for completion. Verify `.team-review/02-interconnect.md` exists and contains the required anchors (`## Contracts`, `## Invariants`, `## Domain Rules`, `## Assumptions`, `## Integration Hot-Spots`, `## Reviewer Hints`). Empty sections are acceptable but the anchors must exist.
4. Mark `phase_1b_interconnect` complete.
