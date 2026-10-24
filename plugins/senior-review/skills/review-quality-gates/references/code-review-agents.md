## Existing analysis compatibility

Coordinators load `codebase-map:map-method` and apply `references/migration.md`
before root lookup or dispatch. Workers use supplied bindings and never migrate
roots. Failed resolution or a still-legacy `.codebase-xray` path blocks the
dependent operation; preserve archives and run IDs.

# Code-review worker briefs

The computed roster selects reviewers. This reference supplies handoff rules for
the native code-review variant, not another selection policy or a copied set of
specialist checklists. The light shape uses its own single-reviewer method.

## Shared handoff

For each validated job, supply its canonical member bodies through the host's
declared isolated binding once. The roster's identities are coverage obligations,
not additional dispatches. Supply:

- Run/review identity, exact candidate snapshot, target and authorized scope.
- Intent, applicable project instructions and the actual comparison when present.
- Source and evidence-pack paths, allowed context and scoped knowledge bindings.
- The shared Intent, Diff Scope, hypothesis and premise-provenance instructions
  from the code-review variant. Missing comparison remains an explicit gap.
- One assigned intermediate report path (`job.output_path`) and the required delivery outcome.

Load the role body once. Let it inspect the relevant full source, callers,
contracts and counterevidence; share artifact paths instead of copying whole
files into every prompt. Independent discovery receives no peer findings.
Reuse the evidence pack without rerunning settled checks or copying tool output
into another finding. Preserve tool-reported results in the run's existing
accounting and declare unavailable measurements.

The role owns its method and native output. Include the native finding envelope
required by review-consolidation's `references/stack-findings.md`, preserving
source role, evidence, severity, confidence and premise provenance. Report a
supported no-findings outcome with coverage/gaps; a blank response is not a
result. Reviewers return their intermediate report; the coordinator owns the
consolidated report and any PR description. No application edits are authorized.

## Canonical owners

Legacy letters are labels for existing consumers, never run conditions. Resolve
every roster identity through the compiled catalog, including entries beyond
this table. An absent example row cannot suppress a selected reviewer.

| Label | Responsibility | Canonical role |
|---|---|---|
| A | General correctness and local design | `senior-review:code-auditor` |
| B | Application security | `senior-review:security-auditor` |
| B2 | Source cleanup / workspace hygiene | `senior-review:cleanup-auditor` / `repo-hygiene:workspace-auditor`, each only when selected |
| C | UI timing and races | `senior-review:ui-race-auditor` |
| F | Test protection and suite quality | `testing:test-suite-auditor` |
| G | API contracts | `senior-review:api-contract-auditor` |
| H / M | Migration data validity and persistent-state integrity | `senior-review:data-integrity-auditor`, one delivery |
| J | Concept ownership, prior art and abstraction | `abstraction-architect:abstraction-architect-agent` |
| L | Temporal resilience | `senior-review:temporal-resilience-auditor` |
| N | Resource ownership and release | `senior-review:resource-lifecycle-auditor` |
| O | Accessibility and usable interaction paths | `senior-review:accessibility-auditor` |
| P | General performance, queries and cost | `senior-review:performance-auditor` |
| Q | Operability, rollout and recovery | `senior-review:operability-auditor` |
| Other selected roles | Startup cycles, distributed flows, logic and premises | Their registered `senior-review` bodies |
| Stack bindings | React, TypeScript, client platforms, Python and dependencies | Preparation's `references/stack-dimensions.md` |

The code auditor retains the generalist floor and its canonical local correctness
checks. Specialist selection adds focused inspection; it does not paste the
specialist's checklist into the generalist. General performance belongs to P,
React rendering to its React owner, client compatibility to platform, and service
operation to Q. Migration data validity, startup order, query cost and mixed-version
rollout keep their distinct owners. Record an out-of-mandate lead with its evidence
and owner; do not create another worker or claim that owner completed a review.

## Required input adaptations

**Testing (F).** Supply affected source modules and their tests, not only changed
test files. Use no-run semantics in this review: D2 to D8 cover tests owned by
those modules, while D1/D9 statistics remain suite-wide context. Reuse provided
CI or runtime evidence at its recorded snapshot and mark unmeasured facts. Include
the selected testing members within their validated job; keep product, oracle, environment
and flaky failures distinct. Missing protection is reviewable even if no test
file changed.

**Abstraction (J).** Include the selected abstraction members within their validated
job. Supply `mode: diff`, `codebase_path`, the resolved map run
or `xray_path: none`, `concept_index_path`, `changed_files`, `report_path: job.output_path` and the
review's severity floor. Its prior-art search may read the whole codebase; the
diff anchors findings rather than confining that search to changed files. Its
canonical role governs absent/stale map and concept-index evidence. Do not use
the `.codebase-map/` root as an invented run locator.

**Cleanup and workspace (B2).** Supply the prepared review perimeter. Source
cleanup uses `cleanup-auditor`'s canonical method; filesystem/git facts use
`repo-hygiene:repo-hygiene` through its selected workspace reviewer. Code-review's
lite perimeter stays diff-scoped: source D1 and applicable VCS checks on added
files. Team-review's full audit does not become an implicit extra pass here.
Preserve introduced, exposed and preexisting classifications from the native
variant; an unchanged evidence line does not alone make an exposed defect
ineligible. Never remove artifacts during review.

**Premises.** Supply the declared mode. Blind derivation receives no map or peer
conclusions. Its existing same-snapshot discovery delivery is accounted once;
verification lenses receive only their explicitly assigned claims in fresh
contexts. A worker's mode is not inferred from a legacy letter.

## Explicit support work

`project-protocol:isolated-worker` remains the binding for method-only providers
and the enclosing method's declared verification/critic work. Being present in
`support` permits dispatch; it does not create another discovery reviewer.

If the enclosing method explicitly needs history analysis (legacy E), assign
bounded paths/hunks and one output to that worker. Inspect the relevant commits
and regressions, reuse preparation's history, and prove how the candidate
reintroduces or contradicts a prior behavior. Age, churn and author count alone
are not defects. Never launch a history pass merely because a diff exists.

## Delivery barrier

Record all expected reviewer identities and assigned outputs before dispatch.
Collect each as delivered or failed, including explicit no-findings reports.
Retain failed/missing coverage and provenance in the ledger; a stopped turn or
an available role is not a delivered review. Consolidation and its required
verification gates run only after this accounting is complete.
