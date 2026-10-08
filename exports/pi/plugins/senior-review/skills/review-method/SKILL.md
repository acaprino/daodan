---
name: review-method
description: >
  Unified review engine for code-review, team-review and pr-review, including signal-selected stack specialists.
---

# Unified review method

Input: variant, target/flags, output root; optional same-snapshot `prepared` bundle.
Output: native report and the project-result envelope. Do not call a second
workflow as an executor.

The consuming workflow declares the named reviewer inventory in `dispatch.roles`
and isolated inline workers in its sidecar. Any inline lens, critic, history,
hygiene or minimal-fix brief in the references uses the canonical
`project-protocol:isolated-worker` binding supplied by the host harness. A
`general-purpose` label describes that inline task; it is not another agent ID.

1. Load the `senior-review:review-preparation` skill, unless a same-snapshot prepared bundle
   was supplied. Validate its target, run identity and snapshot before reusing it.
   Complete missing stack selection through review-preparation before dispatch;
   Validate the prepared knowledge selection's schema, candidate/run/snapshot,
   content and metadata fingerprints, scope and assigned delivery IDs as well.
   A missing or stale knowledge binding requires preparation against this exact
   candidate before dispatch, not reuse of an older-schema or another-run bundle.
   a reused bundle needs activation evidence or a skip/gap reason for all three
   stack dimensions. Do not prepare another run or dispatch a reviewer twice.
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

Read-only review preserves the workspace. Before any accepted fix, load
`project-protocol:project-protocol` for execution preflight, authorizations,
baseline, candidate gate and owned recovery. Commit and publication are separate
authorizations; a request for review is not authorization to publish.
