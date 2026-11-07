## Execution requirements

This workflow fans out over the dimensions its detection step selects. Dispatch, scheduling and result
collection belong to the host branch-review harness; these units own the order. What this
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
| 0 | Resolve the target (0), detect dimensions (0b), discover source-derived evidence without consuming Codebase Map analyses or knowledge leads (0c) | `.team-review/00-scope.md`, `01a-review-knowledge-leads.md` |
| 1 | Context from the complete map's tools, questions the change raises, selection of controls and composition of jobs | `01-context.md`, `02-selection.md` |
| 2 | One isolated worker per validated job, with canonical member checks; every finding declares its load-bearing premise and provenance | assigned job reports |
| 3 | Delivery barrier: every job and member delivers findings or an explicit no-findings result | ledger |
| 4 | Consolidation weighted by provenance, verification panel (4b), completeness critic (4c) | `99-consolidated.md` |
| 5 | Report and cleanup | final report |

**Raw inputs**: `--no-context` withholds shared analytical context. It does not
remove a selected role or verification gate. Supply
source-derived scoped semantic context when a selected logic reviewer needs it;
if a required input cannot be supplied under the requested restriction, record
the review as incomplete instead of silently dropping that reviewer.

## Skills to Load

Before starting, invoke these skills to inform the review process:
- `senior-review:review-quality-gates`: provenance rule and reviewer conventions in its core; its `references/context-sharing.md` for anchor routing before dispatch
- `senior-review:defect-taxonomy`: 140+ defect subcategories with CWE/OWASP mappings (includes `logic-integrity.md`)

## Pre-flight Checks

Verify the [Codebase Map prerequisite](../../../README.md#prerequisito) before
Phase 0. Scope resolution and Phase 1 use the existing run's indexes and tools;
no phase of this pipeline analyzes the project to establish the prerequisite.

1. Confirm the harness can dispatch isolated reviewers; stop if it cannot.
2. Parse `$ARGUMENTS`:
   - `<target>`: file path, directory, git diff range (e.g., `main...HEAD`), PR number (e.g., `#123`), or a request in words (e.g., `the checkout flow`)
   - `--reviewers`: comma-separated dimensions OR `auto` (default: `auto`)
   - `--base-branch`: base branch for diff comparison (default: `main`)
   - `--all`: record a request for all dimensions; reconcile it with the computed roster before dispatch
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
       "phase_1_context": "pending",
       "phase_1_questions": "pending",
       "phase_1_selection": "pending",
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
   - **File/Directory given as the target**: use as-is for review scope
   - **Git diff range**: `git diff {range} --name-only` to get changed files
   - **PR number**: `gh pr diff {number} --name-only` to get changed files
   - **Plan, specification or document**: the paths, symbols and contracts it names, resolved against the current tree, are the review scope; the file itself is the artifact under review
   - **A request in words** (a module, feature, function, error, domain term, or a sentence that names files): follow "Request to files" below; the resulting files are judged as current content unless the request names a comparison
2. Collect the actual diff when the target has a comparison. For a file/directory
   target retain the named contents and scope; never manufacture a diff, silently
   replace it with uncommitted changes, or claim an empty diff covers the target.
   Missing comparison or unsupported roster preparation remains an explicit gap.
3. Collect the list of changed file paths and extensions for Phase 0b.
4. State the candidate's intent in one sentence (what it changes and why), from the task, the PR description or the commit messages; if no source supports one, ask the caller before any dispatch and record `intent: unknown` when none comes. That sentence is the intent every worker prompt pastes.
5. Write `.team-review/00-scope.md` with target, intent, files, flags and, for a request in words, its outcome, the `file:line` that shows each file and any gap. Append a `## Pre-review work tree` section containing the output of `git status --porcelain` at this moment: the Phase 5 workspace hygiene check diffs against it. Mark phase complete in `state.json`.

### Request to files

Translate the request into the files to review. Which tool answers which
question: `references/tools-guide.md` of `codebase-map:map`.

1. **Find.** Take the names from the request: files, functions, modules,
   errors, terms. For each, the cheapest tool: explicit file → none; module →
   `codebase_map_modules`; name or word → `codebase_map_search`; flow →
   `codebase_map_graph`, one hop at a time from files already confirmed. Retry
   an empty search once with a synonym; a missing or stale index is not an
   empty search, it is a missing prerequisite.
2. **Confirm.** Respect explicit limits ("only this file", a diff); otherwise
   names are starting points and include only files pertinent to the request,
   with the line that shows it: `codebase_map_outline` for symbols,
   `codebase_map_read` only the part that decides. A request about a change
   includes the callers it affects (`codebase_map_edit_impact`). The graph does
   not see dynamic links or copies: do not invent them, search by name and read;
   if they cannot be confirmed, say so.
3. **Stop** when evidence suffices, when no leads remain, or at about 6
   queries and 10 reads. Always say why.
4. **Answer** with one of three outcomes: `resolved` (the files, each with its
   evidence); `partial` (the files found, what the request still needs and why); `clarify`
   (the request may mean two different things: the candidates and the question).

`resolved` and `partial` continue with the files found; a `partial` gap stays in
`00-scope.md` and in the final report's coverage. `clarify` asks the caller before
any dispatch; without an answer nothing is dispatched.

The scope is what the review judges; what it reads to judge is Phase 1 context.
Use the run's indexes and source only: the coordinator reads no Codebase Map
analysis artifacts before Phase 0c completes. Everything else is the reviewer's
judgment, stated.

## Phase 0b: Bind the computed reviewer selection

Use the roster produced by `references/candidate-grounding.md` for this exact
candidate. Its `roster` supplies required coverage; validated `jobs` from
`references/composition.md` are the dispatch units. `support` permits the
method's separate context and verification workers. Neither this reference nor
an example below adds an always-on reviewer, lowers a floor or creates a support
task merely because its role is allowed. The light shape uses its own method.

Resolve every selected identity through the catalog `scripts/composition.py
catalog` writes from `plugin.toml`. Bind its canonical role or declared method, prerequisites, scope,
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

Runs inline before required blind derivation or context work. It collects source-derived leads even when shared analytical context is withheld. Structural indexes used for target resolution may locate source; module descriptions and proposals are locating hints, never behavioral premises or evidence for a lead. This phase derives its leads by reading repository sources, tests and documents.

**The coordinator must not read Codebase Map analysis artifacts (`01..07.md`), semantic cards or generated knowledge leads before Phase 0c completes**, including mirrors and earlier runs. Codebase Map's knowledge leads enter in Phase 1, Step 1, as supported descriptions or hypotheses, and nowhere earlier. This permits index-based localization in Phase 0 without treating shared analysis as independent discovery.

1. Read `CLAUDE.md`, `AGENTS.md` and equivalent project instruction files, and follow any navigation rule they state. If the project says a specific file is where to look first to find where a concept lives, open that file before opening any code. Discover the conventions from the repository itself, never from a prior Codebase Map run.
2. Extract the concepts, domains and symbols the diff touches. Names of changed functions, classes, modules and config keys are the starting set; add the domain nouns that appear in the diff's own strings and comments.
3. For each concept, search the project's indexes and documentation for a relevant entry, and search the tests for behaviour that encodes it.
4. Collect runtime evidence the user or the run supplies: session logs, timing breakdowns, traces and metrics named in the request or the run record. Record their paths in the evidence pack and route latency/cost hypotheses to performance, failure-over-time hypotheses to temporal resilience, and service diagnosis/recovery hypotheses to operability when those roles are selected, with the artifacts as declared inputs. Runtime evidence never enters by inference: an artifact nobody supplied is a recorded gap, and an assertion about observed runtime behaviour or a runtime value without one stays a gap rather than becoming a finding. A mechanism demonstrated statically from the code in scope, with its trigger and quantities labelled `derived`, remains reportable without runtime artifacts; the two evidence classes never substitute for each other. When the request is an observed runtime symptom with logs and no change to assess, stop preparation and route the work to the investigation method instead of reviewing a diff that does not carry the defect.
5. Write `.team-review/01a-review-knowledge-leads.md`.

**This file is immutable once written.** No later phase appends to it: Phase 1 cites its rows and records in `01-context.md` what Codebase Map's own leads add or contradict.

**Output:** `.team-review/01a-review-knowledge-leads.md`

```markdown
# Review Knowledge Leads

> Leads, not truth. Immutable once written.
> Source-derived pointers, not inherited Codebase Map knowledge leads or analytical conclusions.

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

## Phase 1: Context, Questions, Selection

The coordinator runs the three steps below in its own context, with the Codebase Map tools of the complete run resolved by the prerequisite. Nothing is dispatched in this phase. Record each output path in `state.json` and mark `phase_1_context`, `phase_1_questions` and `phase_1_selection` complete. Phase 2 reads `01-context.md` and `02-selection.md`; `02-interconnect.md` and `01-knowledge-provenance.md` are no longer produced and must not be required.

### Step 1: Context

Output: `.team-review/01-context.md`. Start from the request and the diff, or from the Phase 0 perimeter when there is no diff.

1. Touched symbols: `codebase_map_symbols_at` on the changed ranges.
2. Callers and neighbours: `codebase_map_edit_impact` (one hop) and `codebase_map_graph` on the touched symbols. When a tool fails, use text search (`codebase_map_search`, `git grep`) and write `fallback: text search` beside every reference it produced.
3. Contracts and tests: `codebase_map_search` and `codebase_map_read` for the callers' expectations, the docstrings, and the tests that exercise the touched symbols. Write `no test exercises <symbol>` when that is the case.

Every reference carries path, line range and content version (run id or commit). Keep three sections apart: `## Static facts` (tool-reported), `## Supported descriptions` (behaviour the cited code shows), `## Hypotheses` (including contradictions between sources, both sides cited). Do not expand the whole graph: stop once the callers that depend on the change and their tests are covered, and list what was left out under `## Not covered`.

### Step 2: Questions

Append `## Questions` to `01-context.md`: one question per behaviour the change can break, each with the context reference that motivates it. Language and framework steer the search; alone they raise no question and no reviewer. A change with no question is recorded as such, with the reason.

### Step 3: Selection and composition

Output: `.team-review/02-selection.md`.

1. Candidates are the catalog roles (`composition.py catalog`, members in `CATALOG.json`); micro skills join them when they exist. The baseline of every stack the change touches is mandatory: when the catalog has none, write `baseline missing: <stack>` as a declared gap.
2. Read each candidate's role body before deciding. Record per candidate: `applicable` (to which question), `not applicable`, or `insufficient evidence` (what is missing). Names and tags decide nothing.
3. A question with no applicable control stays listed, with a specific assignment for the reviewer.
4. Compose jobs: one job while the questions share the context. Add a reviewer only for a separate context, an uncovered competence, or a justified independent verification, and write the reason. The number of controls never sets the number of agents. `review_roster.py compute` still provides the tier and the verification policy; the members come from this step and are bound with `composition.py bind`.

```markdown
# Selection

## Questions
| Id | Question | Reference | Control | Status |

## Baselines
| Stack | Control | Status |

## Jobs
| Job | Questions | Reviewer | Reason for a separate job |
```
