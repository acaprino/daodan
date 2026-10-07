## Phase 2: Adversarial Review (parallel)

1. There is no team-creation step. The host harness dispatches each reviewer as this phase requires and records every one as `delivered` or `failed`.
2. For each selected dimension (always-on + detected conditional), dispatch the **most specialized agent** from the table below, each reviewer in its own isolated context.

### Dimension-to-agent mapping

| Dimension | Agent |
|-----------|---------------|
| Security | `senior-review:security-auditor` |
| Architecture (+ failure flows, patterns, scoring) | `senior-review:code-auditor` |
| **Logic integrity (contracts/invariants/domain rules)** | `senior-review:logic-integrity-auditor` |
| **Structural entropy (duplicated knowledge, competing owners, redundant representation, derivable state, missed unification, prior art, abstraction fitness)** | `abstraction-architect:abstraction-architect-agent` |
| Codebase hygiene (full pass: dead code, assets, deps, docs, lifecycle archaeology) | `senior-review:cleanup-auditor` |
| Workspace hygiene (garbage, tracked build output, .gitignore, scratch, doc-assets, git state) | `repo-hygiene:workspace-auditor` |
| UI race conditions | `senior-review:ui-race-auditor` |
| General performance | `senior-review:code-auditor` |
| Distributed flows | `senior-review:distributed-flow-auditor` |
| Circular dependencies | `senior-review:chicken-egg-detector` |
| Temporal resilience (failure-over-time) | `senior-review:temporal-resilience-auditor` |
| Data integrity (persistence semantics) | `senior-review:data-integrity-auditor` |
| Resource lifecycle (ownership and release) | `senior-review:resource-lifecycle-auditor` |
| Testing quality | `testing:test-suite-auditor` |
| API contracts | `senior-review:api-contract-auditor` |
| Data migrations | `senior-review:data-integrity-auditor` |

### Reviewer prompt template (context-aware)

Every reviewer receives the same structural prompt. The key addition vs the old parallel-only mode is the **context paths**.

```
You are reviewing for the {dimension} dimension.

## Target
[Insert contents of .team-review/00-scope.md]

## Diff
{diff content}

## Context files (read these before analyzing code)
- X-ray output: $XRAY_RUN_DIR (see 01-structure.md, 02-interfaces.md, 05-risks.md)
- Interconnect map: .team-review/02-interconnect.md
- Knowledge provenance: .team-review/01-knowledge-provenance.md

### Epistemic status of the shared context

The shared context is NOT ground truth. It is an index of hypotheses produced by
one upstream observer.

- Claims marked `verified` may be reused directly.
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
  the X-ray output or the interconnect map, it is `shared-context`, even if
  your finding never cites an anchor. `mixed` means part of the premise rests on
  shared context and part on evidence you derived yourself. Declare `independent`
  only when you re-derived the whole premise from code, tests or documents you
  read yourself.

Write your output to .team-review/findings-{dimension}.md using the structured format your agent prescribes.
```

If `--no-context` was set, omit the "Context files" and "Reviewer Hints" sections and do NOT spawn the `logic-integrity-auditor`.

**Structural entropy dimension addendum.** `abstraction-architect:abstraction-architect-agent` takes named inputs rather than a free-form dimension prompt. Append this block to its prompt:

```
mode: diff
codebase_path: {target root}
xray_path: {$XRAY_RUN_DIR when Phase 1a ran and produced output, otherwise "none"}
concept_index_path: {target root}/.abstraction-architect/concept-index.json
changed_files: {the same file list used to build the diff above}
report_path: .team-review/findings-abstraction.md
severity_floor: medium
```

Four things about this reviewer, because they invert the default reviewer contract:

- Its search space is the **whole codebase**, not the diff. The diff is only the anchor; the existing representation it is hunting for is by definition in files that did not change. Do not scope it to the changed files.
- It runs fine on `--depth=lite` output, since it consumes only `01-structure.md` and `02-interfaces.md`. Do not force `--deep` on its account.
- `--no-context` does NOT skip it (that rule removes only `logic-integrity-auditor`). It runs with `xray_path: none` and degrades to Glob plus Grep, reporting the reduced confidence in its Gaps section.
- It reads a **concept index** at `.abstraction-architect/concept-index.json` when one exists, which is what makes its knowledge-track dimensions (duplicated domain knowledge, competing sources of truth, redundant representation, duplicated state) worth running on a diff. The index is produced by `/abstraction-architect:audit` in global mode. When it is absent or stale the reviewer degrades to diff-anchored discovery and declares the reduced coverage; it never blocks. This reviewer never writes the index.

**Testing dimension addendum.** `testing:test-suite-auditor` partly inverts the default reviewer contract. Append this to its prompt:

```
Scope: run D2 to D8 only on tests owned by the changed modules; keep D1/D9
statistics suite-wide for context. Do NOT run the full suite inside this
review (no-run semantics): reuse metrics from CI history or existing report
artifacts, and mark anything unmeasured as such. Findings in this command's
severity format. Write your output to .team-review/findings-testing.md.
```

Two notes on why: a review is diff-anchored, so a whole-suite execution would dominate the phase's wall clock for findings mostly outside the diff; and suite-wide inventory statistics still matter because parallel-file and cross-layer-duplicate findings are invisible when only the changed test file is read.

### The workspace-hygiene dimension

This dimension is not a `senior-review` agent. Dispatch the `repo-hygiene:workspace-auditor`
agent in its own isolated context. It owns every check the filesystem and git
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

Write your output to .team-review/findings-workspace-hygiene.md.
```

Its perimeter and `cleanup-auditor`'s do not overlap, so Phase 4 consolidation
has nothing to deduplicate between them. A finding appearing in both reports is
a boundary violation to investigate, not an `echo` to fold.

### Dispatch

Dispatch each reviewer with:

- name: `{dimension}-reviewer` (e.g., "security-reviewer", "logic-integrity-reviewer")
- agent: from the table above
- task: "Review {target} for {dimension} issues", with the template above as its prompt, `{dimension}` and anchors substituted

The dispatched reviewers are the expected set that Phase 3's delivery barrier waits on.

Mark `phase_2_review` as `in_progress`.

## Phase 3: Monitor and Collect

1. Hold the delivery barrier: wait until every dispatched reviewer is recorded `delivered` or `failed`.
2. As each reviewer delivers, verify `.team-review/findings-{dimension}.md` was written. If a reviewer failed to write its output file, take the output it returned and save it manually to that path.
3. Track progress: "{completed}/{total} reviews complete".
4. **Delivery gate** (per the `senior-review:review-quality-gates` skill, section `## Delivery Gate`): consolidation does not start until every spawned reviewer has either delivered its findings file or delivered an explicit no-findings report. A reviewer that has not delivered by a reasonable deadline gets one reminder, through whatever channel the host offers to a running worker. If it stays silent, record it `failed`, take whatever output it returned, save it to the findings path marked `[undelivered -- collected by orchestrator]`, and record the dimension as degraded in the report. A silently missing dimension is never presented as a clean one.
5. Mark `phase_2_review` complete, `phase_3_consolidation` in_progress.


## Raw mode (`--no-context`)

Reviewers receive the target and diff only. No context artifact is produced or
distributed.

- Phases skipped: 0c, 1a, 1c, 1d, 1b
- Not spawned: `logic-integrity-auditor`, `premise-auditor` (either mode)
- Every finding is `independent` by construction, so Lens 0 never fires and
  consolidation never reports an echo
- Output identical in structure to the pre-pipeline version

Use it for targets under roughly 100 LOC where the context pipeline costs more
than it returns, for quick scans, and when X-ray produces no usable output.

`--skip-interconnect` was removed in senior-review 9.0.0. Use `--no-context`.
