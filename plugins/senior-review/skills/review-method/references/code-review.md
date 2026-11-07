## Step 3: Run Parallel Review Agents

Run the validated jobs through worker dispatch, in isolated contexts.

### Shared Instructions for All Agents

Include these instructions in every agent prompt:

```
## Intent
[paste the one-sentence intent from preparation's Phase 0, or `intent: unknown`]

## Diff Scope & Pre-existing Classification

For changeset basis, classify findings under the base policy into three tiers:

- **Primary** -- lines added or modified in the diff. Your main focus. Full confidence.
- **Secondary** -- unchanged code in the same function/block as a changed line. Report
  if the diff makes the issue newly relevant, noting the interaction.
- **Pre-existing** -- issues in unchanged code unrelated to the diff. Mark these with
  `[PRE-EXISTING]` prefix. They are reported separately and do NOT count toward the verdict.

Rule: if you'd flag the same issue on an identical diff without the surrounding file,
it's pre-existing. If the diff makes it newly relevant, it's secondary.
An unchanged evidence line alone does not make an exposed defect ineligible.
For content basis, admit evidenced defects in the named scope, including
preexisting ones, under the requested snapshot's policy. For claims basis, judge
the document's assertions under its method; do not reinterpret it as a source audit.

## Finding fields

Use the fields and definitions of `## Deliver once` in the specialist review
conventions (`reviewer-common.md`) delivered with this job's `common` binding.

The evidence pack is attached to this brief. Do not restate a tool line and do
not spend reading on what a tool already settled; report what tools cannot see.
```

Dispatch the validated jobs in isolated contexts using the host's supported
coordination mechanism. Preserve the roster's floor, support requirements and verification
level. The native variant supplies finding classification and report structure;
it does not add always-on workers or shrink the prepared set.

### Dispatch

Dispatch the validated jobs under preparation's
`references/composition.md`, once each. Keep the computed roster as required
coverage, not a second dispatch list. Preserve every member's canonical method,
scope and result in the same ledger. The role-oriented instructions below describe
each member's obligations within its assigned job.

Load `senior-review:review-quality-gates` and its
`references/code-review-agents.md` for the shared handoff and input adaptations.
Each selected member executes its canonical body. Resolve all identities through
the compiled catalog, including accessibility, general performance and operability;
API and migration reviews use their registered owners rather than duplicate
inline checklists. Stack and method bindings come from preparation's
`references/stack-dimensions.md`.

Record each expected job, its member identities, scope, snapshot and assigned intermediate output
before dispatch. Premise verification stays per finding, in the verification
panel, with its own inputs. Preserve required isolation and omit peer findings from independent discovery.
A missing catalog binding, prerequisite or delivery remains a failed or incomplete
review, never an omitted dimension or a clean result. Account for every expected
job and member before consolidation. The coordinator alone writes the native final report.
