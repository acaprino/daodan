---
name: review-method
description: >
  Unified review engine: the light review and the branch review (variants team-review and pr-review, and code-review), including signal-selected stack specialists.
  TRIGGER WHEN: the user asks to review current changes, a commit, a file, a plan, a specification, a document, a branch or a pull request for defects, or /daodan:review-changes, /daodan:review-branch or a lifecycle review phase runs a review.
  DO NOT TRIGGER WHEN: establishing the root cause of a reported failure without reviewing an artifact (use investigation-method), or removing dead code (use application-cleanup-method).
---

# Unified review method

Input: variant, target/flags, output root; optional same-snapshot `prepared` bundle;
optional `shape` (`light` for one wave's diff, `branch` for the whole candidate) and
`target-kind` (`changeset`, `plan`, `spec`, `doc`), both resolved by preparation
when absent.
Output: native report and the project-result envelope.

**Shape `light`:** read `references/light.md` in this skill and nothing else
of this method. Shape `branch` runs variant `team-review`, or `pr-review` on a
pull request, through the steps below.

Do not delegate execution
to a second workflow or a nested lifecycle scheduler. In team-review Phase 1a,
the coordinator executes the `codebase-map:map-method` analyze entry's preflight,
answerable checkpoints, delivery check and publication decision. Its
`codebase-map:map-analyst` runs the requested phases in one isolated context
through this workflow's declared host harness. Loading the method alone executes
no phase; use the analyst as a role, never as a skill or declarative `invoke`.
Keep one review preparation and final report owner; required workers still run
in isolated contexts through the declared host bindings.

The consuming workflow declares the named reviewer inventory in `dispatch.roles`
and isolated inline workers in its sidecar. Any inline lens, critic, history,
hygiene or minimal-fix brief in the references uses the canonical
`project-protocol:isolated-worker` binding supplied by the host harness, never
a generic host role name. Keep scope, authorization,
budget, expected report path and delivered or failed outcome for every brief.

1. Load the `senior-review:review-preparation` skill, unless a same-snapshot prepared
   bundle was supplied. Before reusing one, validate its target, run identity,
   snapshot and knowledge selection (schema, candidate, fingerprints, scope,
   assigned delivery IDs), and require activation evidence or a skip or gap
   reason for all three stack dimensions; anything missing or stale is prepared
   again against this exact candidate. Do not prepare another run or dispatch a
   reviewer twice.
2. Read `references/<variant>.md` in this skill. Dispatch the full prepared selection,
   including applicable React, TypeScript and platform reviewers, in the same batch.
   Core role inputs and prompts remain canonical in `senior-review:review-quality-gates`;
   stack roles use their canonical provider definitions and preparation's shared inputs.
   Preserve the prepared `knowledge_selection` and assign each worker only its scoped
   `knowledge_ids`, selection fingerprint and exact catalog load/reference bindings.
   Each worker loads its assigned knowledge as read-only input, applies it against
   code evidence, and returns `knowledge_usage` with scope, worker, hashes, references
   and application explanation. Account for task-specific knowledge lenses in this
   same dispatch and delivery ledger. No worker receives peer findings before delivery.
   Use isolated contexts and the host's supplied coordination mechanism. Account
   for every selected worker before starting consolidation.
3. Load the `senior-review:review-consolidation` skill with all native reviewer
   results. Do not run the reference's output/fix tail until consolidation finishes.
4. For code review, read `references/code-review-delivery.md` only after all core
   and stack results have passed native consolidation and verification. Team
   and PR report delivery remains in their consolidation references. Run delivery
   and any authorized fix steps once. Application subtraction loads
   `senior-review:application-cleanup-method`; significant semantic refactors are
   returned to the caller's development plan and are never delegated to cleanup.

Read-only review preserves application files and preexisting edits.
The coordinator alone may perform the project-bound Codebase Map preflight
before dispatch: move an idle legacy archive intact and write only bound
relocation metadata. This bounded exception authorizes no application changes,
analysis run, worker migration or generic filesystem move.
Before any accepted fix, load
`project-protocol:project-protocol` for execution preflight, authorizations,
baseline, candidate gate and owned recovery. Commit and publication are separate
authorizations; a request for review is not authorization to publish.
