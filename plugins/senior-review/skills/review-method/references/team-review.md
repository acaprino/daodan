## Phase 2: Adversarial Review (parallel)

1. There is no team-creation step. The host harness dispatches each reviewer as this phase requires and records every one as `delivered` or `failed`.
2. Dispatch every validated job exactly once under preparation's
   `references/composition.md`, using its bound worker role and canonical member
   bodies in an isolated context. The roster supplies required coverage. The mapping
   below names owners, not extra activation rules. Resolve catalog entries even
   when a future registered identity has no example row here. A missing binding
   is a failed delivery, never permission to omit that reviewer.
3. The jobs come from Phase 1 (`.team-review/02-selection.md`): each job
   carries its selected reviewer and covers the whole scope, or its `paths` when
   `coverage` splits the scope into groups. The mapping below
   names dimension owners; it adds no job to that selection. Premise verification
   happens per finding, in Phase 4b, with its own inputs and contexts.

### Dimension-to-agent mapping

| Dimension | Agent |
|-----------|---------------|
| Security | `senior-review:security-auditor` |
| General correctness and local design | `senior-review:code-auditor` |
| **Logic integrity (contracts/invariants/domain rules)** | `senior-review:logic-integrity-auditor` |
| **Structural entropy (duplicated knowledge, competing owners, redundant representation, derivable state, missed unification, prior art, abstraction fitness)** | `senior-review:prior-art-auditor` |
| Codebase hygiene (full pass: dead code, assets, deps, docs, lifecycle archaeology) | `senior-review:cleanup-auditor` |
| Workspace hygiene (garbage, tracked build output, .gitignore, scratch, doc-assets, git state) | `senior-review:workspace-hygiene-auditor`, also a member of `cleanup-auditor` |
| UI race conditions | `senior-review:ui-race-auditor` |
| Accessibility and usable interaction paths | `senior-review:accessibility-auditor` |
| General performance and cost | `senior-review:performance-auditor` |
| Service operability, rollout and recovery | `senior-review:operability-auditor` |
| Distributed flows | `senior-review:distributed-flow-auditor` |
| Circular dependencies | `senior-review:chicken-egg-detector` |
| Temporal resilience (failure-over-time) | `senior-review:temporal-resilience-auditor` |
| Data integrity (persistence semantics) | `senior-review:data-integrity-auditor` |
| Resource lifecycle (ownership and release) | `senior-review:resource-lifecycle-auditor` |
| Testing quality | `senior-review:testing-auditor` |
| API contracts | `senior-review:api-contract-auditor` |
| Migration data validity | `senior-review:data-integrity-auditor` (same delivery as data integrity) |
| Premise discovery or document claim check | `senior-review:premise-auditor` (declared mode) |
| React rendering | `senior-review:react-auditor` |
| TypeScript/type contracts | `senior-review:typescript-auditor` |
| Tauri desktop shell | `senior-review:tauri-auditor` |
| Browser, PWA and mobile compatibility | no platform specialist beyond Tauri exists; record activation evidence and declare the gap |
| Python / dependencies | `senior-review:dependency-auditor` for manifests/lockfiles; no Python-specific specialist exists; a declared gap |

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
- Context: .team-review/01-context.md (review object and relevant source references)
- Selection: .team-review/02-selection.md (the selected reviewers and why)
- Codebase Map: the complete run named in the context; query its tools for anything the context does not cover

### Epistemic status of the shared context

The shared context is NOT ground truth. It is an index of hypotheses produced by
one upstream observer.

- References guide source reading; confirm any premise against current source
  before using it in a finding.
- Descriptions and hypotheses are not ground truth. Independently re-derive them
  before using them as a finding's premise.
- Actively search for code paths, tests or documents that contradict the context.
  Finding one is a result, not a failure.
- Silence in the context is not evidence of absence. A concern the map does not
  mention may still be real; look anyway.

Your perimeter is the whole scope or, for a job with paths, `Assigned files: {job.paths}`: conclude on those files under your mandate and read whatever else they need. Report findings, completed checks and gaps.

## Instructions
Follow your agent definition's analysis phases, knowledge-base loading, output format, and severity classification. Cite file:line for every finding.

## Finding fields

Use the fields and definitions of `## Deliver once` in the specialist review
conventions (`reviewer-common.md`) delivered with this job's `common` binding.

Write the one report to the prepared job.output_path using the native structured format, retaining every assigned member's findings and coverage. A job with paths writes it as the JSON reviewer-result of `## Deliver once`, with `read` and `partial`.
```

If `--no-context` was set, omit shared analytical context and reviewer hints.
Keep the required roster and provide source-derived scoped semantic context to a
selected logic reviewer. Missing required inputs remain an explicit incomplete
delivery; they do not authorize dropping that role.

**Structural entropy addendum.** `prior-art-auditor` searches the whole codebase through the complete map run and anchors findings to the diff; supply the run, not an index of concepts.

**Testing addendum.** `testing-auditor` works with no-run semantics: supply the affected source modules with their tests, the runner configuration and any recorded run or coverage evidence at its snapshot. A review is diff-anchored, so a whole-suite execution would dominate the phase for findings mostly outside the diff; suite-wide inventory still matters because duplicate test files and uncollected tests are invisible when only the changed test file is read.

**Workspace hygiene addendum.** `workspace-hygiene-auditor` decides only what the filesystem and git decide; supply the tracked file list, the effective ignore rules and the pre-review work tree from `.team-review/00-scope.md`. Source-comprehensible cleanup stays with `senior-review:cleanup-auditor`.

### Dispatch

Dispatch validated jobs under preparation's
`references/composition.md`. They are the expected delivery set, retaining every
computed member/scope obligation and its canonical method. Do not also dispatch
the roster's thematic identities. The role-oriented handoff below applies to each
member within its assigned job.

Dispatch each job with:

- name: the prepared job ID
- agent: the job's bound worker role, resolved through the active host mechanism
- task: the prepared job body once, with the scoped template inputs above

The validated jobs and their member/scope obligations are the expected set that
Phase 3's delivery barrier waits on. Record each expected job and assigned output before dispatch. A dispatch
failure or missing output cannot shrink that set; a completed turn alone is not
a delivered result.

Mark `phase_2_review` as `in_progress`.

## Phase 3: Monitor and Collect

1. Hold the delivery barrier: wait until every dispatched reviewer is recorded `delivered` or `failed`.
2. As each job delivers, verify its assigned report (the JSON result for a job with paths) exists and accounts for every expected member. If a worker returned the complete report without saving it, preserve that exact output at the assigned path; missing member coverage still fails the delivery gate.
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
