## Phase 4: Consolidation

Apply these deduplication and calibration rules:

1. **Deduplicate**: merge findings that reference the same `file:line` + same issue. Credit all reviewers.
2. **Co-locate**: same `file:line` but different issues -> keep separate, tag as co-located.
3. **Resolve severity conflicts**: use the higher rating.
4. **Cross-reference, weighted by provenance.** Per `## Shared-Context Provenance Rule` in the `senior-review:review-quality-gates` skill, agreement is only corroboration when the agreeing findings did not inherit the same premise.
   - Findings that agree and are all `independent`, or whose load-bearing premises are disjoint: **corroborated**. Report as a likely-real root cause.
   - Findings that agree and share the same `shared-context` premise: **echo**. Report under the finding as `Echo: N dimensions agreed from the shared premise "[premise text]"`. This raises no confidence and no severity, and it is not evidence that the finding is real.
   - Mixed sets: corroboration counts only the independent members.
5. **Collect `[MAP-GAP]` findings**: any logic-integrity finding carrying the `[MAP-GAP]` marker is also listed in the report as an interconnect-map coverage gap, so the mapper's blind spot is recorded alongside the defect it hid.
6. **Organize by severity**: Critical, High, Medium, Low.

Write `.team-review/99-consolidated.md`. Mark `phase_3_consolidation` complete.

## Phase 4b: Adversarial Verification

Skip this phase if `--fast` was passed (mark `phase_4b_verification` as `skipped`). Otherwise drive the panel exactly per the `senior-review:review-quality-gates` skill, section `## Adversarial Verification Panel`.

1. Apply the confidence floor: select consolidated findings with confidence `>= 50%`. team-review reviewers emit confidence in their findings; if a finding lacks a score, treat it as 60% (in-band) so it is not silently skipped.
2. Apply the selection rule from the skill:
   - If `--rigorous`, or 25 or fewer findings survive: verify all selected findings.
   - Otherwise (more than 25 findings, no `--rigorous`): narrow to stakes + uncertainty band per the skill, and record the count of findings left `unverified (cost-guard)`.
3. **Lens 0 first.** For each finding to verify whose `premise_provenance` is `shared-context` or `mixed`, **or whose declared premise carries a universal or negative quantifier (`no`, `never`, `cannot`, `always`, `only`) at any provenance**, spawn lens 0 (`senior-review:premise-auditor`, mode 2, inheriting the session model) using the Lens 0 prompt from the skill, with the X-ray line resolved to `$XRAY_RUN_DIR`. Apply the skill's Lens 0 resolution table: a `REFUTED` verdict targeting `PREMISE` discards the finding (`filtered: premise-refuted`) without spawning lenses 1-2; targeting `SUPPORT` on `mixed` provenance strikes the shared leg and restates the finding from the surviving independent evidence before it proceeds; targeting `SUPPORT` on `shared-context` provenance discards it the same way. `UNCERTAIN` and `HOLDS` proceed to lenses 1-2, `UNCERTAIN` tagged `premise-contested`. Findings declared `independent` whose premise carries no such quantifier skip lens 0 entirely and proceed directly to lenses 1-2.
4. For each finding that reaches this step, spawn lenses 1 and 2 in parallel using the lens prompts from the skill (`general-purpose`; inherit the session model; `run_in_background: true`), then spawn lens 3 (`model: sonnet`) only for findings that survive them, per the skill's gated-lens rule. Substitute the finding, diff, and full file content into each prompt.
5. Apply the survival rule from the skill: survive if `>= 2` of lenses 1-2 vote REAL; discard (`filtered`) if `>= 2` vote FALSE_POSITIVE; tie or fewer-than-2-verdicts means survive and mark `contested`. Final severity is the lens-3 vote when confirmed real, else the original.
6. Write `.team-review/98-verification.md`: one row per verified finding with the per-lens verdicts (including, for findings that reached lens 0, its verdict, refutation target, and counterexample), final severity, and flag (`verified` / `contested` / `filtered: premise-refuted` / `filtered`), plus a trailing count of `unverified (cost-guard)` findings.
7. Update `99-consolidated.md` to drop `filtered` findings, apply recalibrated severities, and tag `contested`, `premise-contested`, and `unverified (cost-guard)` findings.
8. Mark `phase_4b_verification` complete.

## Phase 4c: Completeness Critic

Skip this phase if `--fast` was passed (mark `phase_4c_critic` as `skipped`). Otherwise drive the critic exactly per the `senior-review:review-quality-gates` skill, section `## Completeness Critic`.

1. Spawn one critic agent (`general-purpose`) with the critic prompt from the skill. Pass the verified findings (post-4b), `.team-review/00-scope.md`, the dimensions that ran, and the context paths (`$XRAY_RUN_DIR` and `.team-review/02-interconnect.md`, or "none" under `--no-context`).
2. Write the critic output to `.team-review/97-coverage-gaps.md`.
3. If the critic names a single high-risk uncovered area under `## Recommended follow-up` AND neither the cost guard nor `--fast` applies: spawn ONE targeted reviewer (the most specialized agent for that area, per the Phase 2 dimension-to-agent table) for one round, scoped to the files the critic named. Route its findings back through Phase 4 (dedup) and Phase 4b (verification). Do this at most once.
4. If the cost guard applies, degrade to report-only: keep `97-coverage-gaps.md`, spawn no follow-up, and note the skip.
5. Mark `phase_4c_critic` complete.

## Phase 5: Report and Cleanup

1. Present the consolidated report to the user:

   ```
   ## Code Review Report: {target}

   Session: .team-review/
   Context: X-ray ({lite|full}) + interconnect map ({anchor count} anchors)
   Reviewed by: {dimensions} ({N} reviewers)
   Files reviewed: {count}
   Verification: {verified} verified, {filtered} false positives, {contested} contested, {premise_refuted} premise-refuted, {premise_contested} premise-contested{cost_guard_note}

   ### Critical ({count})
   [findings with file:line + category + map anchor where applicable]

   ### High ({count})
   [findings...]

   ### Medium ({count})
   [findings...]

   ### Low ({count})
   [findings...]

   ### Summary
   Total findings: {count} (Critical: N, High: N, Medium: N, Low: N)
   Coverage gaps: see .team-review/97-coverage-gaps.md ({gap_count} gaps, {followup} follow-up round)
   Map utilization: {count} findings cite an anchor ({pct}%, operational)
   Independent premise reconstruction: {ipr_count} findings ({ipr_pct}%)
   Premise challenge: {pc_count} of {eligible} eligible premises attacked by Lens 0
   Corroborated findings: {n_corroborated} (independent agreement)
   Echoes: {n_echo} (agreement inherited from a shared premise, not corroboration)
   Pipeline time: Phase 1: {t1}, Phase 2: {t2}, total: {total}

   ### Coverage Gaps
   [paste the ## Coverage Gaps list from .team-review/97-coverage-gaps.md]
   ```

   Where `{cost_guard_note}` is `, narrowed to stakes+band (N unverified)` when the cost guard fired, else empty.

2. **Workspace hygiene check**: follow `senior-review:review-quality-gates` section
   `## Delivery Gate`. Compare the recorded snapshot and owned artifact manifest,
   preserving foreign/changed files, resume data and unresolved evidence. Preserve
   experiment results before any permitted temporary cleanup. Return persistent
   retention candidates to consolidate; status alone never grants ownership.
3. End the run. Every dispatched reviewer has been recorded `delivered` or `failed` by now, no reviewer may still be writing after the report is presented, and the harness owns whatever cleanup its workers need.
4. Close the native report stages in `state.json`. The common run can be complete
   only when the protocol's delivery and gate rules pass. A failed or missing
   reviewer remains explicit degraded coverage; a finished report does not turn
   that failed delivery into success.
5. Inform the user that detailed findings and context are preserved in `.team-review/` for future reference (do not auto-delete).
