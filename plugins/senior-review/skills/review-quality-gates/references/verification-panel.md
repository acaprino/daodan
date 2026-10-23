# Verification panel and completeness critic

Consolidation unit of `senior-review:review-quality-gates`; account for every
selected reviewer first. Prompts: `references/panel-and-critic-prompts.md`.

## Adversarial Verification Panel

For each selected deduplicated finding, dispatch one isolated worker per lens
through the consuming workflow's host harness. Lens 0 uses declared
`senior-review:premise-auditor`; lenses 1-3 use only declared
`project-protocol:isolated-worker`, with Section 2's lens-specific briefs.
Include owned scope, authorization, budget, declared inputs and expected report
path. Ledger every delivered/failed outcome; no peer findings before independent
delivery. Inherit the session model; overrides require explicit user request and
supported host binding, never invented host-specific aliases.

### Lens gating and Lens 0 resolution

1. **Lens 0 (Premise Challenge, Mode 2 of `senior-review:premise-auditor`) runs first**, gated on `premise_provenance` (`shared-context` or `mixed`, or missing when pipeline ran) **or** any declared premise containing a universal/negative quantifier (`no`, `never`, `cannot`, `always`, `only`).
   - `REFUTED` (`PREMISE`), or `REFUTED` (`SUPPORT` + `shared-context`): finding discarded (`filtered: premise-refuted`), lenses 1-2 not spawned.
   - `REFUTED` (`SUPPORT` + `mixed`): strike the shared leg, restate from independent evidence, run lenses 1-2.
   - `UNCERTAIN` (including Lens 0 errors or `REFUTED` without `file:line`): proceeds to lenses 1-2 tagged `premise-contested`.
   - `HOLDS`: proceeds to lenses 1-2 unchanged.
   - `premise_form: non-compliant` is recorded in the verification file regardless of verdict.
   - **Absence claims too:** universal assurance over shared/multi-instance state
     receives Lens 0. Its premise is instance/path scope: verify multiplicity and
     alternate paths. `REFUTED` becomes a contested coverage gap naming the
     counterexample path, never an opposite defect without its own lenses 1-2.
2. **Lenses 1 (Reachability) and 2 (False-Positive Causes)** run independently on findings surviving Lens 0:
   - **>= 2 REAL**: finding survives.
   - **>= 2 FALSE_POSITIVE**: finding discarded (`filtered`, count reported).
   - **Tie (1 REAL / 1 FALSE_POSITIVE) or < 2 valid verdicts**: finding survives marked `contested` (fail-open).
3. **Lens 3 (Severity Calibration)** is gated and runs only on findings that survive Lenses 1-2. Final severity is Lens 3's `severity_vote` when confirmed real, else the original reviewer severity.

### Selection and Cost Guard

- **Normal (default-on):** every deduplicated finding with confidence `>= 50%`.
- **Cost guard (> 25 survivors without `--rigorous`):** verify Critical/High plus
  Medium/Low at 50-75% confidence or conflicting reviewer severities. Pass others
  through as `unverified (cost-guard)`; disclose narrowing. Finding count proxies
  token spend.
- **`--rigorous`:** verify all findings above the floor. **`--fast`:** skip panel and critic.

## Completeness Critic

After verification, one isolated `project-protocol:isolated-worker` critic uses the consuming workflow's host binding and the prompt in `references/panel-and-critic-prompts.md` (Section 3) to emit `## Coverage Gaps` across five categories:
1. **Dimensions not run** warranted by scope
2. **Files in scope cited by no reviewer**
3. **Unverified assumptions** in the interconnect map unaddressed by findings
4. **High-risk hot-spots** (`05-risks.md` or Integration Hot-Spots) with zero findings
5. **Findings closed on metrics alone** without stating user-visible consequences or with `derived`-only numbers

If the critic identifies a high-risk uncovered area (and cost guard / `--fast` is not active), spawn **one** targeted reviewer for a **single** follow-up round; its findings pass through deduplication and the verification panel.
