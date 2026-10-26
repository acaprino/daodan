> Wherever `<arguments>` appears below, substitute the text the user typed after the prompt name.

<daodan_host_binding host="copilot">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Copilot binding: repository reads use search, writes use edit, shell execution uses
runCommands and network fetch uses fetch in the adapter's tool allowlist. Custom
agent dispatch uses the agent allowlist alias; the current CLI documents a task
dispatch tool. Call the mechanism actually registered in this session, not an
allowlist alias assumed to be a callable tool.
Use each registered tool's input fields; Claude's subagent_type, role and
run_in_background fields are not a portable dispatch schema. Dispatch only the
custom agent named by the generated owner-qualified binding and agents allowlist.
An omitted tools restriction retains host defaults; an explicit list constrains
the worker and does not grant omitted shell, write or MCP tools.
Skills use their exact installed registry identity; workflows are prompt entries.
A dispatched workflow also has its generated <workflow>-coordinator custom agent.
Required foreign providers use Copilot's marketplace/install commands:
copilot plugin marketplace add <source>, then copilot plugin install <provider>@<marketplace>.
Register plugin-declared MCP server commands in this host's MCP configuration as
the generated note directs. Registration and a dependency declaration alone do
not demonstrate that browser/server tools are callable by the selected worker.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Coordinator MCP allowances use <declared-server>/* for only the package's named
servers. This requires actual server registration and tool discovery; it grants
no undeclared server and does not prove MCP is callable in an installed run.
Schema reference: https://docs.github.com/en/copilot/reference/custom-agents-configuration

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



## Existing analysis compatibility

Coordinators load `codebase-map:map-method` and apply `references/migration.md`
before root lookup or dispatch. Workers never migrate roots: use only its
`migrate_root.py resolve` for supplied bindings. Propagate returned paths.
Failed migration/resolution or a still-legacy `.codebase-xray` path blocks the
dependent operation; preserve archives and run IDs.

## Execution requirements

This workflow fans out over the dimensions its detection step selects. Dispatch, scheduling and result
collection belong to the harness of `/daodan:review-branch`; these units own the order. What this
workflow requires of any harness is fixed and mandatory:

- every job runs in its own context and never reads another job's result
- exactly the validated jobs are dispatched, once each, preserving every selected member/scope obligation
- every expected job and member is recorded `delivered` or `failed` before anything is consolidated
- cross-examination runs after that barrier, in fresh contexts
- only the consolidation phase writes the final report

If the host cannot run jobs in isolated contexts, stop and say so. Compatible
discovery members may share their validated job; independent derivation and
verification never share discovery contexts or peer results.

# Team Review (Pipeline)

| Phase | Work | Output |
|---|---|---|
| 0 | Resolve the target (0), detect dimensions (0b), discover the evidence this review needs without reading any Codebase Map output (0c) | `.team-review/00-scope.md`, `01a-review-knowledge-leads.md` |
| 1 | Codebase Map analysis (1a) and blind premise derivation (1c) in parallel, joined (1d), then the interconnect map (1b) | `01b-independent-claims.md`, `01-knowledge-provenance.md`, `02-interconnect.md` |
| 2 | One isolated worker per validated job, with canonical member checks; every finding declares its load-bearing premise and provenance | assigned job reports |
| 3 | Delivery barrier: every job and member delivers findings or an explicit no-findings result | ledger |
| 4 | Consolidation weighted by provenance, verification panel (4b), completeness critic (4c) | `99-consolidated.md` |
| 5 | Report and cleanup | final report |

**Raw inputs**: `--no-context` withholds shared analytical context. It does not
remove a selected role, required blind derivation or verification gate. Supply
source-derived scoped semantic context when a selected logic reviewer needs it;
if a required input cannot be supplied under the requested restriction, record
the review as incomplete instead of silently dropping that reviewer.

## Skills to Load

Before starting, invoke these skills to inform the review process:
- `senior-review:review-quality-gates`: provenance rule and reviewer conventions in its core; its `references/context-sharing.md` for anchor routing before dispatch
- `senior-review:defect-taxonomy`: 140+ defect subcategories with CWE/OWASP mappings (includes `logic-integrity.md`)

## Pre-flight Checks

1. Confirm the harness can dispatch isolated reviewers; stop if it cannot.
2. Parse `<arguments>`:
   - `<target>`: file path, directory, git diff range (e.g., `main...HEAD`), or PR number (e.g., `#123`)
   - `--reviewers`: comma-separated dimensions OR `auto` (default: `auto`)
   - `--base-branch`: base branch for diff comparison (default: `main`)
   - `--all`: record a request for all dimensions; reconcile it with the computed roster before dispatch
   - `--deep`: run Phase 1a `codebase-map` in full mode (default: `--depth=lite`)
   - `--no-context`: withhold shared analytical context without removing required roles or gates
   - `--fast`: request reduced optional verification work; retain every gate required by the roster
   - `--rigorous`: verify every finding above the confidence floor, ignoring the cost-guard cap
3. Check for existing `.team-review/state.json`:
   - If present with `status: "in_progress"`: ask user whether to resume or start fresh (archive to `.team-review-<ISO-timestamp>/`).
   - If present with `status: "complete"`: ask whether to archive and start fresh.
   - If absent: proceed to new session.
4. Initialize `.team-review/` with `state.json`:

   ```json
   {
     "target": "<arguments>",
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
2. Collect the actual diff when the target has a comparison. For a file/directory
   target retain the named contents and scope; never manufacture a diff, silently
   replace it with uncommitted changes, or claim an empty diff covers the target.
   Missing comparison or unsupported roster preparation remains an explicit gap.
3. Collect the list of changed file paths and extensions for Phase 0b.
4. Write `.team-review/00-scope.md` with target, files, flags. Append a `## Pre-review work tree` section containing the output of `git status --porcelain` at this moment: the Phase 5 workspace hygiene check diffs against it. Mark phase complete in `state.json`.

## Phase 0b: Bind the computed reviewer selection

Use the roster produced by `references/candidate-grounding.md` for this exact
candidate. Its `roster` supplies required coverage; validated `jobs` from
`references/composition.md` are the dispatch units. `support` permits the
method's separate context and verification workers. Neither this reference nor
an example below adds an always-on reviewer, lowers a floor or creates a support
task merely because its role is allowed. The light shape uses its own method.

Resolve every selected identity through the compiled `reviewer-catalog.json` in
this skill. Bind its canonical role or declared method, prerequisites, scope,
snapshot, knowledge assignments and intermediate report path. Include the stack
bindings from `references/stack-dimensions.md` in the same selection and ledger.
A missing binding or prerequisite is a coverage gap or failed delivery, never
permission to omit the selected reviewer or substitute a generalist.

The helper owns automatic activation, including additions and removals. These
boundaries explain the new specialist signals; they are not a second selector:

| Signal in the computed roster | Canonical reviewer | Boundary |
|---|---|---|
| `accessibility` | `senior-review:accessibility-auditor` | Markup, effective styles, keyboard/assistive access and blocked interaction paths, including static CSS changes |
| `performance` | `senior-review:performance-auditor` | Query/index, algorithm, cache, batch, rate-limit and capacity costs; measured claims need actual measurements |
| `operability` | `senior-review:operability-auditor` | Health, telemetry, deployment, flags, mixed-version rollout and recovery |
| `platform` | `platform-engineering:platform-reviewer` | Browser/PWA, mobile and desktop client capabilities, storage and sandbox boundaries |

UI timing stays with `ui-race-auditor`; startup prerequisite cycles stay with
`chicken-egg-detector`; persistent-state validity stays with
`data-integrity-auditor`. A migration may activate several owners because data
validity, startup order, query cost and rollout compatibility are different
questions. Each executes its canonical mandate once in its assigned job.

Inspect the helper's evidence against the actual target. A confirmed relevant
specialist absent from the roster is a selection gap: preserve its source anchor
and report the unmet requested coverage. Do not silently append an unauthorized
role or turn the omission into an inapplicability claim. Legacy `--reviewers` and
`--all` requests are recorded and compared with the computed set; they cannot
remove its floor or bypass the run's allowed dispatch. Apply a caller-supplied
valid selection through the existing preparation contract, not an invented
roster schema or a second selection engine.

Show one compact plan: target and snapshot, roster ID/tier, jobs and member identities
with activation evidence, required support work, skip reasons and gaps, and the
verification level. Context and blind-derivation phases appear only when required
by that plan. Missing providers and dispatch failures are failed deliveries;
unknown applicability is a gap. No install failure is a clean skip.

Mark `phase_0b_detection` complete in `state.json`.

## Phase 0c: Review Evidence Discovery

Runs inline before required blind derivation or context work. It collects source-derived leads even when shared analytical context is withheld. It discovers what evidence is relevant to this review; how the repository documents itself is the Codebase Map's discovery. **It never reads `.codebase-map/` in any form**, the mirror and earlier runs included: the Codebase Map's leads enter at the Phase 1d join and nowhere earlier.

1. Read `CLAUDE.md`, `AGENTS.md` and equivalent project instruction files, and follow any navigation rule they state. If the project says a specific file is where to look first to find where a concept lives, open that file before opening any code. Discover the conventions from the repository itself, never from a prior Codebase Map run.
2. Extract the concepts, domains and symbols the diff touches. Names of changed functions, classes, modules and config keys are the starting set; add the domain nouns that appear in the diff's own strings and comments.
3. For each concept, search the project's indexes and documentation for a relevant entry, and search the tests for behaviour that encodes it.
4. Collect runtime evidence the user or the run supplies: session logs, timing breakdowns, traces and metrics named in the request or the run record. Record their paths in the evidence pack and route latency/cost hypotheses to performance, failure-over-time hypotheses to temporal resilience, and service diagnosis/recovery hypotheses to operability when those roles are selected, with the artifacts as declared inputs. Runtime evidence never enters by inference: an artifact nobody supplied is a recorded gap, and an assertion about observed runtime behaviour or a runtime value without one stays a gap rather than becoming a finding. A mechanism demonstrated statically from the code in scope, with its trigger and quantities labelled `derived`, remains reportable without runtime artifacts; the two evidence classes never substitute for each other. When the request is an observed runtime symptom with logs and no change to assess, stop preparation and route the work to the investigation method instead of reviewing a diff that does not carry the defect.
5. Write `.team-review/01a-review-knowledge-leads.md`.

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

The sub-phases below are listed in execution order. For the complete context pipeline, 1a and 1c start together, 1d joins them, and 1b consumes the joined result. Run only the phases required by the prepared roster.

Follow the prepared roster: Phase 1a runs only when `codebase-map:map-analyst`
is required support, Phase 1b only for `codebase-map:semantic-interconnect-mapper`,
and Phase 1c only when `blind_derivation` is true. Run independent branches in
parallel when both are required. Phase 1d joins their actual deliveries; with no
shared derivation, retain the independent report without inventing a join input.
Record unrequired phases as skipped. A required phase whose inputs conflict with
`--no-context` is unavailable, not silently skipped; the review remains incomplete.
Scoped semantic context can satisfy the logic reviewer's prerequisite without an
interconnect-map dispatch. Preserve the blind derivation's input isolation.

### Phase 1a: Codebase Map Analysis

The review coordinator executes the `codebase-map:map-method` analyze entry's preflight, checkpoints, delivery check and publication decision, and dispatches `codebase-map:map-analyst` in one isolated context for the phases. Loading a method or role body runs nothing. Phase 1c, Phase 1b and every reviewer keep their own isolated contexts.

1. Execute that entry's preflight and coordinator-owned delivery/publication steps against the target. Dispatch `codebase-map:map-analyst` in an isolated context for its requested phases, preserving the canonical scope checkpoints, run binding, output and completion gates:
   - Default mode: `--depth=lite` (structure + interfaces + risks only)
   - If `--deep` flag: full analysis
   - Target scope: the files from Phase 0
2. Read `.codebase-map/runs.json` to resolve the run the workflow just created, and record it in `state.json -> xray` as `run_id`, `run_dir`, `target` and `depth`. Every later phase derives its paths from this block and never from the `.codebase-map/` root. `$XRAY_RUN_DIR` below always means `state.json -> xray.run_dir`. If the run cannot be resolved, halt: an unresolvable provenance is a broken pipeline, not a reason to fall back to the mirror.
3. Verify on completion that at minimum `01-structure.md`, `02-interfaces.md`, and `05-risks.md` exist.
4. Mark `phase_1a_xray` complete.

If the analysis fails or produces no output, halt the pipeline and report a broken installation. Never substitute another worker for the analyst: Phase 1b and Phase 2 depend on the file names and section anchors the analysis itself produces.

### Phase 1c: Independent Premise Derivation (parallel with 1a)

When required, dispatch before reading shared analytical conclusions. Run alongside Phase 1a when that phase is required; this derivation must not see what the Codebase Map derived.

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

3. Account for this delivery. Wait for both 1a and 1c before starting Phase 1d when both branches are required. Mark `phase_1c_premise_audit` complete.

This phase is controlled by `blind_derivation`; a context preference cannot remove it.

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
