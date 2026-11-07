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
| 0 | Resolve the target (0), detect dimensions (0b) | `.team-review/00-scope.md` |
| 1 | Understand the review object within the resolved scope and choose suitable reviewers with clear assignments | `01-context.md`, `02-selection.md` |
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
       "phase_1_context": "pending",
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
Use the run's indexes and source only. Everything else is the reviewer's
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

## Phase 1: Understand the object and select reviewers

The coordinator prepares the review within Phase 0's scope:

1. Read the scoped material and the context needed to understand its purpose, how it works and what matters for the requested review. Use the existing map's tools to locate relevant source, contracts and tests.
2. Consult the available reviewers' mandates and choose the competencies pertinent to that object and intent. Catalog descriptions shortlist candidates; read those candidates' bodies. Languages and extensions guide the choice but do not decide it alone.
3. Give each selected reviewer a clear assignment: what to examine and which parts of the scope to cover, ready to run together in Phase 2. Each assignment names the reference in `01-context.md` (path, lines, version) that motivates it, so a finding can be traced back to it. State any needed competence that is unavailable, including the baseline of a stack the object touches.

Stop when it is clear what is being reviewed and who should review it; defect analysis belongs to the reviewers.

Keep a short description and relevant source references in `01-context.md`, and the selected reviewers and assignments in `02-selection.md`. Finalize and bind that selection through `references/composition.md`. Record both paths and complete `phase_1_context` and `phase_1_selection` in `state.json`. Phase 2 dispatches the prepared jobs.
