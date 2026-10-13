<daodan_host_binding host="pi">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
Core Pi supplies neither subagent nor MCP. Isolated workers require pi-subagents:
pi install npm:pi-subagents. Use that extension's registered subagent schema and
pass the full rendered role body inline. Role skills named <plugin>-<role> are
body resources with automatic invocation disabled, not a built-in named agent.
Workflow prompt entries use /<plugin>-<workflow>; ordinary skills use their exact
registered names. If isolation is mandatory and unavailable, stop the phase.
MCP requires pi-mcp-adapter: pi install npm:pi-mcp-adapter, then register the
generated server command in its supported MCP configuration.
Keep the selected package's full local dependency closure. Provision qualified
foreign providers as skills/resources this runtime can load; Pi does not install
another host's marketplace plugin from a Claude install command.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Kernel <owner>:<skill> references identify the logical provider. Ordinary Pi
skills retain their source frontmatter name, so resolve the actual registered name
and provider path from the active inventory; do not invent a prefixed native ID.

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

Orchestrate a multi-dimensional code review as a **6-phase pipeline**:

0. **Phase 0 -- Scope and Discovery**: resolve the target (0), detect which dimensions the change warrants (0b), and discover independently what evidence this review needs (0c), reading no X-ray output at all.
1. **Phase 1 -- Context Building**: X-ray analysis (1a) runs in parallel with a blind second derivation of the same premises (1c); the two are joined into `01-knowledge-provenance.md` (1d); an interconnect map is built last (1b), covering contracts, invariants, assumptions, domain rules and integration hot-spots. Output goes to `.team-review/`.
2. **Phase 2 -- Adversarial Review (parallel)**: specialized reviewers read the context files and hunt for violations within their dimension. Every finding declares the load-bearing premise it stands on and where that premise came from. Each reviewer writes structured findings to `.team-review/findings-<dim>.md`.
3. **Phase 3 -- Monitor and Collect**: every spawned reviewer delivers findings or an explicit no-findings report before consolidation starts.
4. **Phase 4 (Consolidation)**: findings are deduplicated and organized by severity, with agreement weighted by premise provenance; then the verification panel runs (4b, Lens 0's premise veto first) and the completeness critic asks what the review missed (4c).
5. **Phase 5 -- Report & Cleanup**.

The pipeline lets reviewers find problems that are invisible from local-only inspection: broken implicit contracts, invariant drift, bypass paths to business rules, non-idempotent retry paths, terminal state mutations. Two derivations run side by side in Phase 1 so that the review has a second observer, rather than one observer consulted N times.

**Raw mode**: pass `--no-context` to run the old parallel-only behavior (no Phase 0c, no context phase, no `logic-integrity-auditor`, no `premise-auditor` in either mode).

## Skills to Load

Before starting, invoke these skills to inform the review process:
- `senior-review:review-quality-gates` -- context-sharing pattern, adversarial verification panel, completeness critic
- `senior-review:defect-taxonomy` -- 140+ defect subcategories with CWE/OWASP mappings (includes `logic-integrity.md`)

## Pre-flight Checks

1. Confirm the harness can dispatch isolated reviewers; stop if it cannot.
2. Parse `$ARGUMENTS`:
   - `<target>`: file path, directory, git diff range (e.g., `main...HEAD`), or PR number (e.g., `#123`)
   - `--reviewers`: comma-separated dimensions OR `auto` (default: `auto`)
   - `--base-branch`: base branch for diff comparison (default: `main`)
   - `--all`: force all dimensions regardless of auto-detection
   - `--deep`: run Phase 1a `codebase-xray` in full mode (default: `--depth=lite`)
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

1. Determine target type:
   - **File/Directory**: use as-is for review scope
   - **Git diff range**: `git diff {range} --name-only` to get changed files
   - **PR number**: `gh pr diff {number} --name-only` to get changed files
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
  Phase 1a: codebase-xray (--depth=lite)   |  Phase 1c: premise-auditor (parallel, blind)
  Phase 1d: knowledge reconciliation (inline)
  Phase 1b: codebase-xray:semantic-interconnect-mapper
  Phase 2:  {N} reviewers in parallel
  Phase 3:  monitor and collect (delivery barrier)
  Phase 4:  consolidation, verification (4b), completeness critic (4c)
  Phase 5:  report
```

Every reason on the Skipped line is a statement about the code, never about the install: "no startup code" means the code did not need the dimension. Every agent this command can spawn comes from a plugin `senior-review` declares as a hard dependency, so there is no "plugin not installed" reason and no generic fallback. If a spawn fails with "Agent type not found", stop and report the broken install instead of continuing with a silently reduced review.

Mark `phase_0b_detection` complete in `state.json`.

## Phase 0c: Review Evidence Discovery

Runs inline in the orchestrating context, on every invocation **except** raw mode (`--no-context`). That flag means "give me the raw mode", and a normally-on phase does not override it: `01a-review-knowledge-leads.md` distributed to N reviewers is itself shared context, so keeping this phase alive under the flag would make findings legitimately `shared-context`, let Lens 0 fire, and stop the mode reproducing the pre-pipeline behaviour it exists to provide.

This phase owns discovery of **what evidence is relevant to this review**. X-ray owns discovery of how the repository documents itself. The two are different jobs and the division is deliberate.

**This phase MUST NOT read `.codebase-xray/` in any form**, including the mirror and the output of previous runs. A previous X-ray run is still an X-ray derivation, and admitting one would contaminate the single artifact that has to be demonstrably independent of X-ray. X-ray's leads enter at the Phase 1d join and nowhere earlier.

1. Read `CLAUDE.md`, `AGENTS.md` and equivalent project instruction files, and follow any navigation rule they state. If the project says a specific file is where to look first to find where a concept lives, open that file before opening any code. Discover the conventions from the repository itself, never from a prior X-ray run.
2. Extract the concepts, domains and symbols the diff touches. Names of changed functions, classes, modules and config keys are the starting set; add the domain nouns that appear in the diff's own strings and comments.
3. For each concept, search the project's indexes and documentation for a relevant entry, and search the tests for behaviour that encodes it.
4. Write `.team-review/01a-review-knowledge-leads.md`.

**This file is immutable once written.** No later phase appends to it. X-ray's own leads are joined into a separate derived artifact in Phase 1d, precisely so that the snapshot Phase 1c consumes cannot change underneath it.

**Output:** `.team-review/01a-review-knowledge-leads.md`

```markdown
# Review Knowledge Leads

> Leads, not truth. Immutable once written.
> Discovered by senior-review independently of any X-ray output.

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

### Phase 1a: X-Ray Analysis

> **`codebase-xray:analyze` is the canonical workflow entry of `codebase-xray`, not an agent or executor.** The host lists it as `analyze` (hosts that render workflows as skills suffix it `-workflow`). The review coordinator reads that entry and its `codebase-xray:xray-method`, then directly executes their canonical phases in order in this same context with the resolved arguments. Loading either body alone runs no phase and creates no run directory. This direct composition introduces no declarative `invoke` executor, nested lifecycle scheduler or automatic skill loading. Review preparation runs once and consolidation retains sole final review report ownership. Phase 1c, Phase 1b and all selected reviewers still require their declared isolated worker contexts.

1. Directly execute the `codebase-xray:analyze` entry and its canonical method phase-by-phase against the target, in this coordinator context. Preserve their scope checkpoints, run binding, output and completion gates:
   - Default mode: `--depth=lite` (structure + interfaces + risks only)
   - If `--deep` flag: full analysis
   - Target scope: the files from Phase 0
2. Read `.codebase-xray/runs.json` to resolve the run the workflow just created, and record it in `state.json -> xray` as `run_id`, `run_dir`, `target` and `depth`. Every later phase derives its paths from this block and never from the `.codebase-xray/` root. `$XRAY_RUN_DIR` below always means `state.json -> xray.run_dir`. If the run cannot be resolved, halt: an unresolvable provenance is a broken pipeline, not a reason to fall back to the mirror.
3. Verify on completion that at minimum `01-structure.md`, `02-interfaces.md`, and `05-risks.md` exist.
4. Mark `phase_1a_xray` complete.

If the workflow fails or produces no output, halt the pipeline and report the error: `codebase-xray` is a hard dependency, so a workflow that cannot be loaded is a broken install. Do **not** fall back to spawning a `general-purpose` agent to fake the X-ray output -- the file naming and section anchors that Phase 1b/Phase 2 depend on come from the workflow itself, and a freelance fallback breaks the contract for `logic-integrity-auditor`.

### Phase 1c: Independent Premise Derivation (parallel with 1a)

Spawn immediately when Phase 1a starts. Do not wait for X-ray. The whole point of this phase is that it derives without seeing what X-ray derived.

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

   You have NO access to .codebase-xray/ or to .team-review/02-interconnect.md.
   Neither exists for you. Do not look for them, and report contamination if
   anything in this prompt paraphrases an X-ray conclusion.
   ```

3. Wait for both 1a and 1c before starting Phase 1d. Mark `phase_1c_premise_audit` complete.

Under raw mode (`--no-context`) this phase does not run, because there is no shared derivation for it to be independent of.

### Phase 1d: Knowledge Reconciliation (join)

Runs inline once both 1a and 1c have completed. The premise auditor never compares its own derivation: comparison is done by others, downstream, which is what makes its blindness verifiable rather than merely asserted.

Read `.team-review/01a-review-knowledge-leads.md`, `$XRAY_RUN_DIR/knowledge/documentation-leads.md` and `.team-review/01b-independent-claims.md`. Write:

**Degradation when X-ray produced no leads.** If `$XRAY_RUN_DIR/knowledge/documentation-leads.md` does not exist, record `Inherited from X-Ray: not produced` under that heading and **suppress the asymmetry diagnostic** described below for this run. An absent file is not a discovery gap, and treating it as one would report an X-ray gap on every row: a systematically false signal from the mechanism built to stop false signals. A reused older run, a Phase 0 that failed, and an X-ray version predating Phase 0 all land here. Everything else in this phase proceeds normally: `Missing` and `Disputed` are still computed from `01a` and `01b`.

**Output:** `.team-review/01-knowledge-provenance.md`

```markdown
# Knowledge Provenance

> Derived view, produced after both discovery branches completed.
> The canonical artifact consumed downstream. 01a and 01b are its sources.

## Independently discovered by Senior Review
[rows from 01a-review-knowledge-leads.md]

## Inherited from X-Ray
[rows from $XRAY_RUN_DIR/knowledge/documentation-leads.md]

## Missing
| Concept | In scope because |
|---------|------------------|
| [concept] | [where it appears in the diff] |

## Disputed
| Claim | Independent derivation says | X-ray says |
|-------|------------------------------|------------|
| [claim] | [X at file:line] | [Y at file:line] |
```

**Missing and Disputed are different states and must never collapse into one section.** Absence of evidence is not contradictory evidence.

| Section | Maps to in the interconnect map | Never |
|---|---|---|
| `Missing` | a coverage gap, and `unverified` on any related row | never `disputed`: nobody finding documentation is not two sources disagreeing |
| `Disputed` | `disputed`, both `file:line` sides cited | never silently resolved in favour of either derivation |

Collapsing them would drain `disputed` of the precise meaning the rest of this work depends on, which is that two derivations reached incompatible conclusions and a reviewer must settle it.

**The duty of autonomous rediscovery.** X-ray's documentation leads are an input, never a completeness guarantee. Any concept `01a` carried that X-ray's leads missed stays under `Independently discovered by Senior Review`; a concept neither branch found goes to `Missing`. Neither is downgraded because the other branch was silent. Without this duty, the completeness of X-ray's discovery becomes the next shared premise, which is the failure this pipeline exists to prevent.

Two asymmetries here are diagnostics worth reading, not noise. A row present in `Independently discovered by Senior Review` and absent from `Inherited from X-Ray` means X-ray's discovery had a gap. The reverse means Phase 0c had one. Both are recorded and neither is silently reconciled. Neither is reportable when X-ray produced no leads file at all: the degradation rule above governs that case.

Mark `phase_1d_reconciliation` complete.

### Phase 1b: Semantic Interconnect Mapping

1. Dispatch the `codebase-xray:semantic-interconnect-mapper` agent in its own isolated context.
2. Prompt:

   ```
   Build the interconnect map for this review.

   Target scope: [contents of .team-review/00-scope.md]
   X-ray output: $XRAY_RUN_DIR (files: 01-structure.md, 02-interfaces.md, 05-risks.md, knowledge/documentation-leads.md, ...)
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
