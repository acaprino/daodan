# Verification panel and completeness critic

On-demand unit of `senior-review:review-quality-gates`. Read it at consolidation,
after every selected reviewer is accounted for. The prompts each lens and the
critic receive are in `references/panel-and-critic-prompts.md`.

## Adversarial Verification Panel

Each deduplicated finding selected for verification is judged by up to 4 verifiers (`references/panel-and-critic-prompts.md` Section 2). Dispatch one isolated worker per lens per finding through the consuming workflow's host harness. Lens 0 uses the declared `senior-review:premise-auditor` binding; lenses 1-3 use only the declared `project-protocol:isolated-worker` binding with the lens-specific briefs in `references/panel-and-critic-prompts.md`. Every brief carries the owned scope, authorization, budget, declared inputs and expected report path. Record each delivered or failed outcome in the same delivery ledger. Independent lenses receive no peer findings before their delivery. All lenses inherit the session model by default; apply a supported model override only when explicitly requested by the user and bound by the host harness, never by choosing a host-specific alias here.

### Lens gating and Lens 0 resolution

1. **Lens 0 (Premise Challenge, Mode 2 of `senior-review:premise-auditor`) runs first**, gated on `premise_provenance` (`shared-context` or `mixed`, or missing when pipeline ran) **or** any declared premise containing a universal/negative quantifier (`no`, `never`, `cannot`, `always`, `only`).
   - `REFUTED` (`PREMISE`), or `REFUTED` (`SUPPORT` + `shared-context`): finding discarded (`filtered: premise-refuted`), lenses 1-2 not spawned.
   - `REFUTED` (`SUPPORT` + `mixed`): strike the shared leg, restate from independent evidence, run lenses 1-2.
   - `UNCERTAIN` (including Lens 0 errors or `REFUTED` without `file:line`): proceeds to lenses 1-2 tagged `premise-contested`.
   - `HOLDS`: proceeds to lenses 1-2 unchanged.
   - `premise_form: non-compliant` is recorded in the verification file regardless of verdict.
2. **Lenses 1 (Reachability) and 2 (False-Positive Causes)** run independently on findings surviving Lens 0:
   - **>= 2 REAL**: finding survives.
   - **>= 2 FALSE_POSITIVE**: finding discarded (`filtered`, count reported).
   - **Tie (1 REAL / 1 FALSE_POSITIVE) or < 2 valid verdicts**: finding survives marked `contested` (fail-open).
3. **Lens 3 (Severity Calibration)** is gated and runs only on findings that survive Lenses 1-2. Final severity is Lens 3's `severity_vote` when confirmed real, else the original reviewer severity.

### Selection and Cost Guard

- **Normal (default-on):** every deduplicated finding with confidence `>= 50%`.
- **Under cost guard (> 25 surviving findings and `--rigorous` not set):** verify all Critical/High findings plus Medium/Low in the 50-75% confidence band or with conflicting reviewer severities; pass the rest through tagged `unverified (cost-guard)` and declare the narrowing (the threshold of 25 surviving findings is a finding-count proxy for token spend).
- **`--rigorous`:** verify all findings above the floor. **`--fast`:** skip panel and critic.

## Completeness Critic

After verification, one isolated `project-protocol:isolated-worker` critic uses the consuming workflow's host binding and the prompt in `references/panel-and-critic-prompts.md` (Section 3) to emit `## Coverage Gaps` across five categories:
1. **Dimensions not run** warranted by scope
2. **Files in scope cited by no reviewer**
3. **Unverified assumptions** in the interconnect map unaddressed by findings
4. **High-risk hot-spots** (`05-risks.md` or Integration Hot-Spots) with zero findings
5. **Findings closed on metrics alone** without stating user-visible consequences or with `derived`-only numbers

If the critic identifies a high-risk uncovered area (and cost guard / `--fast` is not active), spawn **one** targeted reviewer for a **single** follow-up round; its findings pass through deduplication and the verification panel.
