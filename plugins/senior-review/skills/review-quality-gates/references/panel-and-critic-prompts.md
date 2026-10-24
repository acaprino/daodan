# Context-Aware Reviewer, Verification Panel, and Completeness Critic Prompts

On-demand reference for `senior-review:review-quality-gates`.

## 1. Context-Aware Reviewer Prompt Template (`team-review`)

```
You are reviewing for the {dimension} dimension.

## Target
[...]

## Diff
[...]

## Context files
- Codebase Map output: $XRAY_RUN_DIR
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
{anchors-for-this-dimension}

## Evidence pack
[tool, version, command, exit status and output path for each deterministic check run on the candidate]

## Instructions
Follow your agent definition's phases and output format. Cite file:line for every finding.
Every finding that relates to a contract/invariant/assumption in the interconnect map should
also cite the map anchor that surfaced the concern. Give every finding its trigger, the
counterevidence you checked, introduced_by_candidate and evidence_class. Do not restate a
tool line from the evidence pack; report what tools cannot see.

Write the one report to the prepared job.output_path, preserving each assigned member's findings and coverage.
```

**Path substitution:** In `team-review`, the Codebase Map line resolves to `$XRAY_RUN_DIR` (the immutable directory of the run Phase 1a started; never the `.codebase-map/` mirror). `code-review` uses its own Codebase Map Context Template (`references/code-review-agents.md`) and reads the `.codebase-map/` mirror when consuming a pre-existing analysis.

---

## 2. Adversarial Verification Panel Prompts

Every isolated panel/critic brief carries `review_basis`, governing policy and its
base or requested snapshot, exact candidate, `conclusion_paths` and `read_scope`.
Supply an actual comparison only for changesets; an empty diff never establishes
the basis. Missing required basis/policy is a coverage gap, not a reason to exclude
a finding as preexisting. Keep these inputs with the assigned finding and output.

Dispatch one isolated worker per lens per finding through the consuming workflow's host harness:
- **Lens 0:** `senior-review:premise-auditor` in Mode 2.
- **Lenses 1-3:** `work-controller:isolated-worker` with the lens-specific briefs below.

### Lens 0 Prompt (Premise Challenge)

```
Mode 2: adversarial premise challenge.

## The Finding
[severity, file:line, description, suggested fix]

## The declared load-bearing premise
[the finding's Load-bearing premise field verbatim, or "none declared"]

## Context available
- Interconnect map: .team-review/02-interconnect.md
- Knowledge provenance: .team-review/01-knowledge-provenance.md
- Codebase Map: $XRAY_RUN_DIR

## Instructions
Follow mode 2 of your agent definition. Attack the premise, not the finding.
Return REFUTED only with a file:line counterexample; without one, return UNCERTAIN.
Decide and state whether the counterexample falsifies the PREMISE itself or only
a piece of shared SUPPORT.
```

*(In `code-review`, Codebase Map resolves to `.codebase-map/`, and interconnect/provenance lines are omitted.)*

### Lens 1 Prompt (Reachability / Correctness)

```
You are verifier LENS 1 of 4 (Reachability / Correctness) for one code-review finding.
Your job: determine whether the described defect REALLY exists and is reachable.

## The Finding
[severity, file:line, description, suggested fix]

## The Diff
[diff for the relevant file]

## Full File Content
[full content of the file containing the finding]

## Hypothesis fields
- Trigger: [the finding's trigger, or "none declared"]
- Counterevidence checked: [the finding's list, or "none declared"]
- introduced_by_candidate: [true / false / not declared]
- evidence_class: [reproduced / tool-reported / measured / derived]

## Reproduction grant
[either "none" or: scratch path, test runner command, base ref, candidate ref]

## Instructions
1. Locate the exact file:line. Is the citation correct?
2. Trace the control/data flow: is the buggy path actually reachable in normal or error execution? Derive the trigger yourself when none was declared.
3. Does the code truly exhibit the described problem, or is the description a misread?
4. With a reproduction grant, write a minimal test at the scratch path, run it on the base and on the candidate, record both outcomes, and remove the file. Passing on the base and failing on the candidate makes the class `reproduced`; failing to show the defect is counterevidence.
Return REAL only if you can point to the concrete lines and the path that triggers the defect.

Respond with EXACTLY:
- Verdict: REAL or FALSE_POSITIVE
- Confidence: 0-100
- Evidence_class: reproduced or tool-reported or measured or derived
- Reason: 1-2 sentences citing file:line
```

### Lens 2 Prompt (False-Positive Causes)

```
You are verifier LENS 2 of 4 (False-Positive Causes) for one code-review finding.
Your job: actively try to REFUTE the finding. Default to FALSE_POSITIVE if uncertain.

## The Finding
[severity, file:line, description, suggested fix]

## The Diff
[diff for the relevant file]

## Full File Content
[full content of the file containing the finding]

## Instructions
Try to explain the flagged code away as one of:
1. Framework convention (Django/FastAPI/pytest/etc. idiom that is correct by design)
2. Intentional design choice consistent with surrounding code or CLAUDE.md
3. For changeset basis only, preexisting code excluded by its base policy because
   the diff neither introduces nor exposes the defect. Content findings within
   the named scope remain eligible; document claims keep their specific method.
4. A misunderstanding of the code's actual behavior or context
Return REAL only if the finding survives refutation on all four counts.

Respond with EXACTLY:
- Verdict: REAL or FALSE_POSITIVE
- Confidence: 0-100
- Reason: 1-2 sentences citing file:line; if FALSE_POSITIVE, name the refutation category
```

### Lens 3 Prompt (Severity Calibration)

```
You are verifier LENS 3 of 4 (Severity Calibration) for one code-review finding.
Assume the finding is REAL. Your only job is to vote the correct severity.

## The Finding
[severity, file:line, description, suggested fix]

## The Diff
[diff for the relevant file]

## Full File Content
[full content of the file containing the finding]

## Calibration criteria
- Critical: data loss, security breach, complete failure; certain or very likely
- High: significant functionality impact or degradation; likely
- Medium: partial impact, workaround exists; possible
- Low: minimal or cosmetic; unlikely

Respond with EXACTLY:
- Verdict: REAL
- Severity_vote: Critical or High or Medium or Low
- Confidence: 0-100
- Reason: 1-2 sentences citing file:line
```

---

## 3. Completeness Critic Prompt

Dispatch one isolated `work-controller:isolated-worker` with:

```
You are the completeness critic for a multi-dimensional code review. Your job is NOT
to find new bugs directly. It is to find what the review did not examine.

## Verified findings
[the consolidated, verified findings]

## Scope
[changed files / target]

## Dimensions that ran
[list]

## Examined coverage
[reviewer report paths: completed checks, no-findings results and declared gaps]

## Context available
[Codebase Map paths and interconnect map path, or "none"]

## Instructions
Produce a "## Coverage Gaps" list across these categories, each item actionable and specific:
1. Dimensions warranted by the scope but not run
2. In-scope files not examined; absence of finding citations alone proves no gap
3. Interconnect assumptions left unverified after the reported checks
4. High-risk hot-spots with missing checks, not merely zero findings
5. Findings closed as acceptable on a metric alone: for each, ask "what does the
   user see when this happens?" -- if the answer is missing or is "nothing, silently",
   re-open it as a gap; also flag any quantitative closure whose number is derived
   from reading the code rather than measured

Then, if and ONLY if one gap is a high-risk uncovered area, name the single most valuable
follow-up: which dimension/agent should review which files. Output it under
"## Recommended follow-up" with one entry, or "## Recommended follow-up: none".
```
