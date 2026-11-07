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
| 0 | Resolve the target (0), compute tier and policy (0b) | `.team-review/00-scope.md` |
| 1 | Understand the review object within the resolved scope and choose suitable reviewers | `01-context.md`, `02-selection.md` |
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
- `senior-review:review-quality-gates`: provenance rule and reviewer conventions in its core
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
       "phase_0b_policy": "pending",
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

## Phase 0b: Compute tier and policy

Run the roster of `references/candidate-grounding.md` for this exact candidate. It fixes the tier, the verification level and the critic; nothing lowers them. Its `roster` and signals are leads for Phase 1, which chooses the reviewers. `--reviewers` and `--all` are recorded as caller requests for Phase 1. A document kind keeps its fixed set (`selection: "automatic"`). The light shape uses its own method.

Mark `phase_0b_policy` complete in `state.json`.

## Phase 1: Understand the object and select reviewers

The coordinator prepares the review within Phase 0's scope:

1. Read the scoped material and the context needed to understand its purpose, how it works and what matters for the requested review. Use the existing map's tools to locate relevant source, contracts and tests.
2. Consult the available reviewers' mandates and choose the competencies pertinent to that object and intent. Catalog descriptions shortlist candidates; read those candidates' bodies. Languages and extensions guide the choice but do not decide it alone.
3. Prepare the selected reviewers to start together in Phase 2, each on the whole scope with its own mandate and the context of step 1. State any needed competence that is unavailable, including the baseline of a stack the object touches.

Stop when it is clear what is being reviewed and who should review it; defect analysis belongs to the reviewers.

Keep a short description and relevant source references in `01-context.md`, and the selected reviewers with the reason for each in `02-selection.md`. Pass the chosen catalog identities to `composition.py bind` as `selection` (`references/composition.md`), with the stack bindings of `references/stack-dimensions.md`. Before dispatch show one compact plan: target and snapshot, tier, selected reviewers and why, verification level, gaps. Record both paths and complete `phase_1_context` and `phase_1_selection` in `state.json`. Phase 2 dispatches the prepared jobs.
