

## Existing analysis compatibility

Coordinators load `codebase-map:map-method` and apply `references/migration.md`
before root lookup or dispatch. Workers never migrate roots: use only its
`migrate_root.py resolve` for supplied bindings. Propagate returned paths.
Failed migration/resolution or a still-legacy `.codebase-xray` path blocks the
dependent operation; preserve archives and run IDs.

## Step 4: Consolidate Findings

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

For changeset basis, separate findings classified `[PRE-EXISTING]` under its base
policy; those excluded by that policy do not count toward the verdict. For content
basis, evidenced defects within the named scope remain eligible even when
preexisting. Claims basis retains its document method. Do not filter a finding
merely because its evidence line is unchanged or `introduced_by_candidate` is false.

### 4d. Sort and preserve evidence

- Sort by severity (Critical first) -> confidence (descending) -> file path -> line number
- Include a score only when the caller requested a defined scoring method and the
  delivered evidence supports it. Otherwise report score as unavailable where a
  legacy view has a score field; do not manufacture one from finding counts.

## Step 4b: Adversarial Verification Panel

Preserve the bound roster and run's required verification level. `--fast` and cost guard may omit only additional optional work; missing required checks leave the review incomplete. Verify findings with the panel defined in the `senior-review:review-quality-gates` skill, file `references/verification-panel.md` (resolve it inside that skill's installed directory), section `## Adversarial Verification Panel`. This replaces the former single-validator step: four independent lenses (premise veto, reachability/correctness, false-positive causes, severity) catch more failure modes than one judge, and the scope widens from Critical/High only to every finding above the confidence floor.

### Selection

- **Default:** every finding with confidence `>= 50%` that survived Step 4b deduplication, regardless of severity.
- **Cost guard** (more than 25 surviving findings AND `--rigorous` not set): preserve every required verification; narrow only additional optional findings to Critical/High plus Medium/Low in the 50-75% confidence band or with conflicting reviewer severity. Tag omitted optional findings `unverified (cost-guard)` and note the narrowing.
- **`--rigorous`:** verify everything above the floor, ignoring the cap.

The cost-guard threshold is a finding-count proxy (no token budget exists in this substrate).

### Panel

**Lens 0 first.** For each selected finding whose `premise_provenance` is `shared-context` or `mixed`, **or whose declared premise carries a universal or negative quantifier (`no`, `never`, `cannot`, `always`, `only`) at any provenance**, dispatch lens 0 through the declared `senior-review:premise-auditor` binding (mode 2, inheriting the session model) using the Lens 0 prompt from the skill, with the Codebase Map line resolved to the `.codebase-map/` mirror and the interconnect-map and knowledge-provenance lines omitted, since this command builds neither. A finding declaring no provenance is format-non-compliant. Account for shared material available or read earlier in the worker context, not only the latest prompt. When shared exposure occurred or cannot be excluded, retain Lens 0 eligibility; declare `independent` only when the whole premise was independently derived. `--no-context` cannot rewrite that history or disable Lens 0 for universal/negative claims. Defaulting the other way would send exactly the non-compliant findings Lens 0 exists to catch straight past the veto. Apply the skill's Lens 0 resolution table: a `REFUTED` verdict targeting `PREMISE` discards the finding (`filtered: premise-refuted`) without spawning lenses 1-2; targeting `SUPPORT` on `mixed` provenance strikes the shared leg and restates the finding from the surviving independent evidence before it proceeds; targeting `SUPPORT` on `shared-context` provenance discards it the same way. `UNCERTAIN` and `HOLDS` proceed to lenses 1-2, `UNCERTAIN` tagged `premise-contested`. Findings declared `independent` whose premise carries no such quantifier skip lens 0 entirely and proceed directly to lenses 1-2.

For each finding that reaches this step, dispatch lenses 1 and 2 independently through the declared `work-controller:isolated-worker` binding using the skill's full lens briefs, owned scope, authorization, budget and expected report paths. Use the host harness's supported topology, inherit the session model and substitute the finding, diff and full file content. Dispatch lens 3 through that same binding only for findings that survive lenses 1-2, per the skill's gated-lens rule: calibrating a finding about to be discarded is spend for nothing.

### Survival rule

A finding discarded by Lens 0 never reaches this rule. Otherwise apply the skill's rule: survive on `>= 2` of lenses 1-2 voting REAL; discard (`filtered`, counted) on `>= 2` FALSE_POSITIVE; tie or fewer-than-2-verdicts means survive and mark `contested`. Final severity is the lens-3 vote when confirmed real, else the original.

**After the panel completes:**
- Drop `filtered` findings; apply recalibrated severities; tag `contested`, `premise-contested`, and `unverified (cost-guard)` findings.
- Add to the report: `Verification: X of Y (4-lens panel), Z false positives, W contested, V premise-refuted, U premise-contested`.

Medium and Low findings are no longer skipped by default: they enter the panel like any other finding above the floor (subject to the cost guard).

## Step 4c: Completeness Critic

Run the critic whenever the bound roster or run requires it. `--fast` may omit only an optional critic; missing required critic delivery remains incomplete. Use the critic defined in the `senior-review:review-quality-gates` skill, file `references/verification-panel.md`, section `## Completeness Critic`.

1. Dispatch one `work-controller:isolated-worker` critic through the host harness with the skill's critic prompt, owned scope, authorization, budget and expected report path. Record its delivered or failed outcome before closing the critic phase. Pass verified findings, changed-file scope, agents that ran, reviewer report paths with completed checks/no-findings results/gaps, and admitted Codebase Map context paths (else "none").
2. If the critic names a single high-risk uncovered area under `## Recommended follow-up`, dispatch at most one targeted round through a permitted roster role, scoped to the named files; route findings through deduplication and required verification. A needed role outside the roster remains a selection gap.
3. Cost guard or `--fast` may omit optional follow-up and retain the gap in the report. This cannot satisfy an unmet required check or delivery; affected coverage remains incomplete.
4. Carry the critic's `## Coverage Gaps` list into the Step 5 report.
