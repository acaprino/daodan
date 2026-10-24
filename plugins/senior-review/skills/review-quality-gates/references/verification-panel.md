# Verification panel and completeness critic

Consolidation unit of `senior-review:review-quality-gates`; account for every
selected reviewer first. Briefs: `references/panel-and-critic-prompts.md`.

Roster/run requirements set minimum panel/critic obligations. `--fast`/cost guard
reduce optional work only. `--no-context` changes inputs, never roster, blind
derivation, Lens 0 eligibility or actual provenance. Missing required evidence/delivery
leaves the run incomplete.

## Adversarial Verification Panel

For each selected deduplicated finding, dispatch isolated lenses through the
consuming workflow's host harness: Lens 0 uses declared
`senior-review:premise-auditor`; lenses 1-3 use declared
`work-controller:isolated-worker`. Briefs carry owned scope, authorization, budget,
inputs and report path. Ledger delivered/failed outcomes. Lenses receive no peer
findings before independent delivery. Inherit session model; overrides require
explicit user request and supported host binding, never invented aliases.

### Lens gating and Lens 0 resolution

1. **Lens 0 runs first** (Premise Challenge, Mode 2): eligible provenance is
   `shared-context`, `mixed`, or missing after pipeline execution; also any
   universal/negative premise (`no`, `never`, `cannot`, `always`, `only`).
   - `REFUTED` (`PREMISE`) or (`SUPPORT` + `shared-context`): discard
     (`filtered: premise-refuted`); do not spawn lenses 1-2.
   - `REFUTED` (`SUPPORT` + `mixed`): strike shared support, restate from
     independent evidence, then lenses 1-2.
   - `UNCERTAIN`, errors or `REFUTED` without `file:line`: lenses 1-2,
     tagged `premise-contested`.
   - `HOLDS`: lenses 1-2 unchanged.
   - Record `premise_form: non-compliant` regardless of verdict.
   - **Absence claims too:** universal assurance over shared/multi-instance state
     receives Lens 0: verify instance/path scope and alternate paths.
     `REFUTED` becomes a contested coverage gap citing the counterexample, never
     an opposite defect without its own lenses 1-2.
2. **Lenses 1 (Reachability) and 2 (False-Positive Causes)** run independently:
   - >= 2 `REAL`: survives.
   - >= 2 `FALSE_POSITIVE`: discard, report filtered count.
   - Tie or < 2 valid verdicts: survives `contested` (fail-open).
3. **Lens 3 (Severity Calibration)**: gated, only after survival.
   Confirmed real: use its `severity_vote`; otherwise retain reviewer severity.

### Selection and Cost Guard

- **Normal:** every deduplicated finding with confidence >= 50%.
- **Cost guard:** > 25 survivors without `--rigorous`. Preserve required
  verification; optional selection retains Critical/High, Medium/Low at 50-75%
  confidence or conflicting severity. Label omitted optional findings
  `unverified (cost-guard)`; disclose narrowing. Count proxies token spend.
- **`--rigorous`:** all above the floor. **`--fast`:** optional panel/critic
  only; never waives required checks or Lens 0 eligibility.

## Completeness Critic

When required or included optionally in preparation, one isolated
`work-controller:isolated-worker` runs after verification through the same host
binding. Prompt: `references/panel-and-critic-prompts.md`, Section 3.
Emit `## Coverage Gaps` for:
1. Warranted dimensions not run.
2. Unexamined scoped files; no citation alone does not prove omission.
3. Unverified interconnect assumptions.
4. Unexamined high-risk hot-spots (`05-risks.md`/Integration Hot-Spots); zero findings alone is not a gap.
5. Findings accepted on derived metrics alone or without user-visible consequences.

For high-risk uncovered scope, allow one targeted follow-up round with an
already-permitted reviewer; deduplicate and verify its findings. Cost guard/`--fast`
suppress optional follow-up only. Required coverage remains incomplete; an
unlisted role is a selection gap, never dispatch authorization.
