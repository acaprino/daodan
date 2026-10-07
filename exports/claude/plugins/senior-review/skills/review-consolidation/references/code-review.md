## Step 4: Consolidate Findings & Extract Score

After all agents complete, run the merge pipeline:

### 4a. Confidence Gating

Apply a three-tier confidence filter to all findings:

| Confidence | Action |
|------------|--------|
| **< 0.50 (< 50%)** | **Suppress** -- finding is speculative, discard it. Record suppressed count. |
| **0.50 - 0.69** | **Flag** -- include in report but mark as low-confidence |
| **>= 0.70** | **Report** -- full confidence, include normally |

### 4b. Deduplication

When multiple agents flag the same issue, merge them:

1. Compute fingerprint: `normalize(file) + line_bucket(line, +-3) + normalize(title)`
2. When fingerprints match:
   - Keep the **highest severity**
   - Keep the **highest confidence** with strongest evidence
   - **Union** the evidence from all agents
   - Weigh the agreement by provenance, per `## Shared-Context Provenance Rule` in the `senior-review:review-quality-gates` skill, instead of just noting which agents flagged it:
     - All agreeing agents report `independent` `premise_provenance`, or their load-bearing premises are disjoint: **corroborated**. Note the agreeing agents; the merge is a likely-real root cause.
     - All agreeing agents share the same `shared-context` premise: **echo**. Note it as `Echo: N agents agreed from the shared premise "[premise text]"`. This raises no confidence and no severity, and it is not evidence the finding is real.
     - Mixed: count only the independent agents toward corroboration.
3. Record the dedup count, split into corroborated merges and echo merges

### 4c. Separate Pre-existing

Pull out findings with `[PRE-EXISTING]` prefix into a separate list. These are reported in their own section and do NOT count toward the verdict.

### 4d. Sort & Score

- Sort by severity (Critical first) -> confidence (descending) -> file path -> line number
- Extract the Code Quality Score from code-auditor (Agent A) directly

## Step 4b: Adversarial Verification Panel

Skip this step if `--fast` was passed. Otherwise verify findings with the 4-lens panel defined in the `senior-review:review-quality-gates` skill, section `## Adversarial Verification Panel`. This replaces the former single-validator step: four independent lenses (premise veto, reachability/correctness, false-positive causes, severity) catch more failure modes than one judge, and the scope widens from Critical/High only to every finding above the confidence floor.

### Selection

- **Default:** every finding with confidence `>= 50%` that survived Step 4b deduplication, regardless of severity.
- **Cost guard** (more than 25 surviving findings AND `--rigorous` not set): narrow to all Critical/High plus any Medium/Low in the 50-75% confidence band or with conflicting reviewer severity. The rest pass through tagged `unverified (cost-guard)`. Note the narrowing in the report.
- **`--rigorous`:** verify everything above the floor, ignoring the cap.

The cost-guard threshold is a finding-count proxy (no token budget exists in this substrate).

### Panel

**Lens 0 first.** For each selected finding whose `premise_provenance` is `shared-context` or `mixed`, **or whose declared premise carries a universal or negative quantifier (`no`, `never`, `cannot`, `always`, `only`) at any provenance**, spawn lens 0 (`role: senior-review:premise-auditor`, mode 2, inheriting the session model) using the Lens 0 prompt from the skill, with the X-ray line resolved to the `.codebase-xray/` mirror and the interconnect-map and knowledge-provenance lines omitted, since this command builds neither. A finding declaring no provenance is `shared-context` whenever `.codebase-xray/` context was injected into the agent prompts, and the report records the agent as format-non-compliant; it is `independent` only when no such context was supplied at all. Defaulting the other way would send exactly the non-compliant findings Lens 0 exists to catch straight past the veto. Apply the skill's Lens 0 resolution table: a `REFUTED` verdict targeting `PREMISE` discards the finding (`filtered: premise-refuted`) without spawning lenses 1-2; targeting `SUPPORT` on `mixed` provenance strikes the shared leg and restates the finding from the surviving independent evidence before it proceeds; targeting `SUPPORT` on `shared-context` provenance discards it the same way. `UNCERTAIN` and `HOLDS` proceed to lenses 1-2, `UNCERTAIN` tagged `premise-contested`. Findings declared `independent` whose premise carries no such quantifier skip lens 0 entirely and proceed directly to lenses 1-2.

For each finding that reaches this step, spawn lenses 1 and 2 in parallel using the lens prompts from the skill (`general-purpose`; inherit the session model; `run_in_background: true`), substituting the finding, the diff, and the full file content. Spawn lens 3 (`model: sonnet`) only for findings that survive lenses 1-2, per the skill's gated-lens rule: calibrating a finding about to be discarded is spend for nothing.

### Survival rule

A finding discarded by Lens 0 never reaches this rule. Otherwise apply the skill's rule: survive on `>= 2` of lenses 1-2 voting REAL; discard (`filtered`, counted) on `>= 2` FALSE_POSITIVE; tie or fewer-than-2-verdicts means survive and mark `contested`. Final severity is the lens-3 vote when confirmed real, else the original.

**After the panel completes:**
- Drop `filtered` findings; apply recalibrated severities; tag `contested`, `premise-contested`, and `unverified (cost-guard)` findings.
- Add to the report: `Verification: X of Y (4-lens panel), Z false positives, W contested, V premise-refuted, U premise-contested`.

Medium and Low findings are no longer skipped by default: they enter the panel like any other finding above the floor (subject to the cost guard).

## Step 4c: Completeness Critic

Skip this step if `--fast` was passed. Otherwise run the critic defined in the `senior-review:review-quality-gates` skill, section `## Completeness Critic`.

1. Spawn one `general-purpose` critic with the skill's critic prompt. Pass the verified findings, the changed-file scope, the agents that ran, and the X-ray context paths if `.codebase-xray/` exists (else "none").
2. If the critic names a single high-risk uncovered area under `## Recommended follow-up` AND the cost guard did not fire: spawn ONE targeted reviewer (the most specialized agent for that area) scoped to the files named, then route its findings back through Step 4 (dedup) and Step 4b (panel). At most one round.
3. Otherwise degrade to report-only.
4. Carry the critic's `## Coverage Gaps` list into the Step 5 report.
