

## Existing analysis compatibility

Coordinators load `codebase-map:map-method` and apply `references/migration.md`
before root lookup or dispatch. Workers never migrate roots: use only its
`migrate_root.py resolve` for supplied bindings. Propagate returned paths.
Failed migration/resolution or a still-legacy `.codebase-xray` path blocks the
dependent operation; preserve archives and run IDs.

## Phase 2: Adversarial Review (parallel)

1. There is no team-creation step. The host harness dispatches each reviewer as this phase requires and records every one as `delivered` or `failed`.
2. Dispatch every validated job exactly once under preparation's
   `references/composition.md`, using its bound worker role and canonical member
   bodies in an isolated context. The roster supplies required coverage. The mapping
   below names owners, not extra activation rules. Resolve catalog entries even
   when a future registered identity has no example row here. A missing binding
   is a failed delivery, never permission to omit that reviewer.
3. Account for Phase 1c's same-snapshot blind premise report as the selected premise
   discovery delivery, rather than launching a second discovery pass. Later
   verification tasks keep their separate inputs, contexts and delivery records.

### Dimension-to-agent mapping

| Dimension | Agent |
|-----------|---------------|
| Security | `senior-review:security-auditor` |
| General correctness and local design | `senior-review:code-auditor` |
| **Logic integrity (contracts/invariants/domain rules)** | `senior-review:logic-integrity-auditor` |
| **Structural entropy (duplicated knowledge, competing owners, redundant representation, derivable state, missed unification, prior art, abstraction fitness)** | `abstraction-architect:abstraction-architect-agent` |
| Codebase hygiene (full pass: dead code, assets, deps, docs, lifecycle archaeology) | `senior-review:cleanup-auditor` |
| Workspace hygiene (garbage, tracked build output, .gitignore, scratch, doc-assets, git state) | `repo-hygiene:workspace-auditor` |
| UI race conditions | `senior-review:ui-race-auditor` |
| Accessibility and usable interaction paths | `senior-review:accessibility-auditor` |
| General performance and cost | `senior-review:performance-auditor` |
| Service operability, rollout and recovery | `senior-review:operability-auditor` |
| Distributed flows | `senior-review:distributed-flow-auditor` |
| Circular dependencies | `senior-review:chicken-egg-detector` |
| Temporal resilience (failure-over-time) | `senior-review:temporal-resilience-auditor` |
| Data integrity (persistence semantics) | `senior-review:data-integrity-auditor` |
| Resource lifecycle (ownership and release) | `senior-review:resource-lifecycle-auditor` |
| Testing quality | `testing:test-suite-auditor` |
| API contracts | `senior-review:api-contract-auditor` |
| Migration data validity | `senior-review:data-integrity-auditor` (same delivery as data integrity) |
| Premise discovery or document claim check | `senior-review:premise-auditor` (declared mode) |
| React rendering | `react-development:react-performance-optimizer` |
| TypeScript/type contracts | `typescript-development:type-safety-auditor` |
| Browser, mobile and desktop compatibility | `platform-engineering:platform-reviewer` |
| Python / dependencies | Catalog method bindings through `project-protocol:isolated-worker`; see preparation's stack bindings |

### Reviewer prompt template (context-aware)

The validated jobs also contain applicable stack dimensions from
review-preparation's `references/stack-dimensions.md`. Their canonical member
methods use the shared template below within those jobs and enter the same
Phase 3 delivery barrier and downstream verification panel.

Build one concise brief per job. Supply its member identities, target, run identity,
snapshot, scope, applicable instructions, evidence/knowledge paths and a unique
intermediate report path. Reference prepared artifacts rather than pasting them
repeatedly. Include only context artifacts that exist and that this worker may
read; independent discovery receives no peer findings. The canonical role owns
its detection method and native output; the shared envelope adds provenance.

```
You are reviewing for the {dimension} dimension.

## Target
[Insert contents of .team-review/00-scope.md]

## Diff
{diff content}

## Context files (read these before analyzing code)
- Codebase Map output: $XRAY_RUN_DIR (see 01-structure.md, 02-interfaces.md, 05-risks.md)
- Interconnect map: .team-review/02-interconnect.md
- Knowledge provenance: .team-review/01-knowledge-provenance.md

### Epistemic status of the shared context

The shared context is NOT ground truth. It is an index of hypotheses produced by
one upstream observer.

- Claims marked `verified` guide source reading; confirm the premise against
  current source before using it in a finding.
- Claims marked `documented`, `unverified` or `disputed` are hypotheses. You MUST
  independently re-derive any such claim before using it as the premise of a finding.
- Actively search for code paths, tests or documents that contradict the context.
  Finding one is a result, not a failure.
- Silence in the context is not evidence of absence. A concern the map does not
  mention may still be real; look anyway.

Per `## Reviewer Hints` in the interconnect map, focus your reading on these anchors:
{anchors-for-this-dimension from the map's Reviewer Hints section}

## Instructions
Follow your agent definition's analysis phases, knowledge-base loading, output format, and severity classification. Cite file:line for every finding.

## Premise declaration (required on every finding)

Every finding carries two extra fields:

- **Load-bearing premise:** the single proposition whose falsity collapses this
  finding. It must be minimal, falsifiable and scoped.
    Bad:  "The implementation is broken."
    Bad:  "Heartbeat handling is incorrect."   (a paraphrase of your finding)
    Good: "No credential-bearing response path exists after registration."
- **premise_provenance:** one of `independent`, `shared-context`, `mixed`.
  This records CAUSAL DEPENDENCE, not citation. If you absorbed the premise from
  the Codebase Map output or the interconnect map, it is `shared-context`, even if
  your finding never cites an anchor. `mixed` means part of the premise rests on
  shared context and part on evidence you derived yourself. Declare `independent`
  only when you re-derived the whole premise from code, tests or documents you
  read yourself.

Write the one report to the prepared job.output_path using the native structured format, retaining every assigned member's findings and coverage.
```

If `--no-context` was set, omit shared analytical context and reviewer hints.
Keep the required roster and provide source-derived scoped semantic context to a
selected logic reviewer. Missing required inputs remain an explicit incomplete
delivery; they do not authorize dropping that role.

**Structural entropy dimension addendum.** Dispatch selected members of `abstraction-architect:abstraction-architect-agent` through their validated jobs. Append this native input contract once per job:

```
mode: diff
codebase_path: {target root}
xray_path: {$XRAY_RUN_DIR when Phase 1a ran and produced output, otherwise "none"}
concept_index_path: {target root}/.abstraction-architect/concept-index.json
changed_files: {the same file list used to build the diff above}
report_path: {prepared job.output_path}
severity_floor: medium
```

Four things about this reviewer, because they invert the default reviewer contract:

- Its search space is the **whole codebase**, not the diff. The diff is only the anchor; the existing representation it is hunting for is by definition in files that did not change. Do not scope it to the changed files.
- It runs fine on `--depth=lite` output, since it consumes only `01-structure.md` and `02-interfaces.md`. Do not force `--deep` on its account.
- `--no-context` does not skip it. It runs with `xray_path: none` and uses source discovery, reporting the missing map evidence in its Gaps section.
- It reads a **concept index** at `.abstraction-architect/concept-index.json` when one exists, which is what makes its knowledge-track dimensions (duplicated domain knowledge, competing sources of truth, redundant representation, duplicated state) worth running on a diff. The index is produced by the audit of `abstraction-architect:abstraction-architect` in global mode (`/daodan:check-health`). When it is absent or stale the reviewer degrades to diff-anchored discovery and declares the reduced coverage; it never blocks. This reviewer never writes the index.

**Testing dimension addendum.** `testing:test-suite-auditor` partly inverts the default reviewer contract. Append this to its prompt:

```
Scope: run D2 to D8 only on tests owned by the changed modules; keep D1/D9
statistics suite-wide for context. Do NOT run the full suite inside this
review (no-run semantics): reuse metrics from CI history or existing report
artifacts, and mark anything unmeasured as such. Findings in this command's
severity format within the one report at the prepared job.output_path.
```

Two notes on why: a review is diff-anchored, so a whole-suite execution would dominate the phase's wall clock for findings mostly outside the diff; and suite-wide inventory statistics still matter because parallel-file and cross-layer-duplicate findings are invisible when only the changed test file is read.

### The workspace-hygiene dimension

This dimension is not a `senior-review` agent. Dispatch the `repo-hygiene:workspace-auditor`
member within its assigned isolated job. It owns every check the filesystem and git
decide without reading a symbol.

```
You are auditing workspace hygiene for a team review of {target}.

Load the repo-hygiene:repo-hygiene skill and run its catalog at the FULL
profile: C1 filesystem garbage, C2 generated artifacts tracked in git,
C3 .gitignore completeness, C4 .gitignore archaeology, C5 scratch and
pipeline-output directories, C6 orphan doc-assets, C7 git auxiliary state.

Report only. Remove nothing, and never run a destructive git command: C7 is
detection-only because a dropped stash or a removed worktree leaves no diff
for any commit to revert.

Anything that needs source comprehension is not yours. Put it under "Not
mine" and name senior-review:cleanup-auditor. The two dimensions are disjoint
by construction, so a finding either of you could have raised means one of
you widened.

Return this member's findings and coverage in the one report at the prepared job.output_path.
```

Its perimeter and `cleanup-auditor`'s do not overlap, so Phase 4 consolidation
has nothing to deduplicate between them. A finding appearing in both reports is
a boundary violation to investigate, not an `echo` to fold.

### Dispatch

Dispatch validated jobs under preparation's
`references/composition.md`. They are the expected delivery set, retaining every
computed member/scope obligation and its canonical method. Do not also dispatch
the roster's thematic identities. The role-oriented handoff below applies to each
member within its assigned job.

Dispatch each job with:

- name: the prepared job ID
- agent: the job's bound worker role, resolved through the active host mechanism
- task: the prepared job body once, with the scoped template inputs above and each member's assigned anchors

The validated jobs and their member/scope obligations are the expected set that
Phase 3's delivery barrier waits on. Record each expected job and assigned output before dispatch. A dispatch
failure or missing output cannot shrink that set; a completed turn alone is not
a delivered result.

Mark `phase_2_review` as `in_progress`.

## Phase 3: Monitor and Collect

1. Hold the delivery barrier: wait until every dispatched reviewer is recorded `delivered` or `failed`.
2. As each job delivers, verify its assigned report exists and accounts for every expected member. If a worker returned the complete report without saving it, preserve that exact output at the assigned path; missing member coverage still fails the delivery gate.
3. Track progress: "{completed}/{total} reviews complete".
4. **Delivery gate** (per the `senior-review:review-quality-gates` skill, section `## Delivery Gate`): consolidation does not start until every spawned reviewer has either delivered its findings file or delivered an explicit no-findings report. A reviewer that has not delivered by a reasonable deadline gets one reminder, through whatever channel the host offers to a running worker. If it stays silent, record it `failed`, take whatever output it returned, save it to the findings path marked `[undelivered -- collected by orchestrator]`, and record the dimension as degraded in the report. A silently missing dimension is never presented as a clean one.
5. Mark `phase_2_review` complete, `phase_3_consolidation` in_progress.


## Raw inputs (`--no-context`)

Withhold shared analytical artifacts while preserving the required roster,
independent derivation and verification gates. Workers read the actual target
and permitted source evidence; they declare the provenance they used rather
than being labelled independent by a flag. Missing required inputs or blocked
support work leave the affected coverage incomplete. Preserve the same report
and delivery contracts. The light shape remains the single-reviewer method in
`references/light.md`; file size alone never selects or removes reviewers.

`--skip-interconnect` was removed in senior-review 9.0.0.
