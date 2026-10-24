# Specialist cases and leaf template

Authoring and qualification use the [manual evaluation protocol](README.md#specialist-qualification).
The [T0 migration matrix](../../docs/superpowers/reports/2026-10-23-reviewer-specialist-migration.md)
maps source controls to proposed owners and cases. Its rows are not independent
tests or reviewer registrations. One fixture may cover several controls when
each mechanism and countercase remains independently observable.

## Minimal leaf body

Keep metadata in the role's existing frontmatter, with its registered name and
`model: inherit`. Keep behavior in Markdown. Fill only the domain-specific
content below; do not repeat the shared envelope, evidence rules or knowledge
protocol in every leaf.

```markdown
# <Specialist responsibility>

Apply the common review conventions supplied with the assignment once.

## Mandate and activation
<One coherent violated contract/mechanism; evidenced triggers that require it.>

## Required input
<Domain requirements, source/configuration and boundaries needed for its checks.
Name prerequisites that cannot be inferred from the brief or shared conventions.>

## Causal checks
<Trace reachable input/state/ordering to the broken invariant and consequence.
Load only the canonical references necessary for these checks.>

## Counterevidence
<Effective guards, alternate paths and valid implementations that refute the claim.>

## Boundaries
<Adjacent mechanisms owned elsewhere; retain their evidence for coordinator routing.>

## Output
<Domain-specific evidence in the existing native report and reviewer-result format.
No second finding list or invented score.>
```

For a `senior-review` leaf, replace the template opening with:

```markdown
Read `${CLAUDE_PLUGIN_ROOT}/skills/review-quality-gates/references/reviewer-common.md`
once per assignment and apply its conventions; reuse them if already supplied.
```

Other providers receive the canonical [common conventions](../../plugins/senior-review/skills/review-quality-gates/references/reviewer-common.md)
in their brief without a reverse dependency. Specialized references stay with
their owner and use installed paths in role bodies. Only request
domain-specific output beyond the common contract when it is needed to judge
the mechanism. Numeric finding confidence is 0–100; native evidence-strength
labels retain their separate meaning.

## Minimal case specification

Reuse `cases/<case>/case.md` and the existing scorecard. For a new specialist
case, use `cases/<provider>-<role>/case.md` when no suitable case exists.
Before executing, write:

- **Coverage and target:** T0 controls, specialist identity, review basis, exact
  files/packet and reproducible setup; declared requirements, conclusion paths,
  admitted read scope and permitted checks.
- **Defect:** reachable trigger, violated contract/mechanism, source evidence and
  expected observable consequence. State which finding qualifies as found or
  partial by mechanism, without requiring wording from the reviewer body.
- **Correct countercase:** a materialized variant where that obligation is
  satisfied, including a guard or valid alternative, and the corresponding
  `must_not_report` claims. A preferred technique's absence alone is not a bug.
- **Other outcomes:** expected completed checks, legitimate gaps or inapplicable
  checks with evidence, delivery behavior and whether runtime exercise is
  required. Keep the oracle outside the reviewer's supplied target and context.

Hashes, model/effort, host, actual output, outcomes, gaps and measured whole-run
cost belong in each run's scorecard and linked artifacts, following README.
Cases state expectations; they do not record a pass before execution.

## Required behavioral probes

Reuse these variations across compatible controls. Execute each specialist's
defect and correct countercase, plus applicable input/delivery variations.
Do not create a separate agent, fixture framework or mandatory production gate
for every row.

| Probe | Setup | Acceptance evidence |
|---|---|---|
| Reachable defect | Materialize the requirement and failing path, including relevant consumer and effective configuration. | Finding establishes trigger, mechanism and consequence from source; scorer matches the independent oracle. |
| Correct alternative / no findings | Materialize a valid implementation with the same obligation; include a guard outside conclusion paths but inside admitted read scope when relevant. | False claim absent; completed checks and examined scope recorded with `findings: []` when no other defects exist. |
| Unavailable required input | Withhold a genuinely required contract, source/configuration or assigned knowledge; distinguish this from optional irrelevant context. | Explicit gap and failed assignment, preserved partial evidence, no clean verdict and no invented product defect. |
| Unavailable dispatch or delivery | Use an unregistered role, unavailable required provider, missing report or empty response. | Dispatch/binding failure or unfulfilled delivery remains visible; another job or scope cannot satisfy it. |
| Knowledge mismatch | Change an assigned body/reference after its binding, or fail its load. | Existing knowledge accounting records failure and required coverage does not pass. |
| Static-only evidence | Permit source inspection and withhold runtime execution. | Static conclusions cite evidence; runtime remains unexercised. A required runtime check remains a gap. |
| Scope and basis | Keep an unchanged defect in a content audit; separately review a delta or document claim under its policy. | Content eligibility, changeset attribution and claim review remain distinct; reading supporting paths does not expand conclusion scope. |

For arbitrary missing domain inputs, the reviewer and coordinator enforce the
expected behavior through their contract and review of the delivery. Catalog,
knowledge and ledger tests prove only the concrete gates they exercise; they
do not establish automatic semantic completeness.

Coverage claims follow actual checks and evidence, never read counts, age,
bytes, grep hits, a named pattern, a budget limit or a finding quota. Route
overlaps by the violated mechanism: static CSS obstruction, UI interleaving,
persistent database races and local-memory races have different owners.

A case that is merely present, a valid envelope or a successful host render
cannot close qualification. Link actual independent scores and unresolved gaps
to the migration matrix. Keep historical outcomes intact when an oracle or
reviewer changes. The disputed payment/retry setups are recorded in
[README](README.md#specialist-qualification) and must be resolved before their
affected outcomes qualify a specialist.
