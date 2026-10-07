---
name: review-method
description: >
  Canonical universal review engine used by code-review, team-review, pr-review and review-plus.
---

# Universal review method

Input: variant, target/flags, output root; optional `prepared` bundle and
`extension_results` with complete delivery ledger. Output: native report and the
project-result envelope. Do not call a second workflow as an executor.

The consuming workflow declares the named reviewer inventory in `dispatch.roles`
and isolated inline workers in its sidecar. Any inline lens, critic, history,
hygiene or minimal-fix brief in the references uses the canonical
`project-protocol:isolated-worker` binding supplied by the host harness. A
`general-purpose` label describes that inline task; it is not another agent ID.

1. Load the `senior-review:review-preparation` skill, unless a same-snapshot prepared bundle
   was supplied. Validate its target, run identity and snapshot before reusing it.
2. Read `references/<variant>.md` in this skill and dispatch its core reviewers.
   Core role inputs and prompts remain canonical in `senior-review:review-quality-gates`.
   Use isolated contexts and the host's supplied coordination mechanism.
3. Load the `senior-review:review-consolidation` skill with all native core and extension
   results. Do not run the reference's output/fix tail until consolidation finishes.
4. For code review, read `references/code-review-delivery.md` only after all core
   and extension results have passed native consolidation and verification. Team
   and PR report delivery remains in their consolidation references. Run delivery
   and any authorized fix steps once. Application subtraction loads
   `senior-review:application-cleanup-method`; significant semantic refactors are
   returned to the caller's development plan and are never delegated to cleanup.

Read-only review preserves the workspace. Before any accepted fix, load
`project-protocol:project-protocol` for execution preflight, authorizations,
baseline, candidate gate and owned recovery. Commit and publication are separate
authorizations; a request for review is not authorization to publish.
