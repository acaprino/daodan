---
name: review-method
description: >
  Unified review engine for code-review, team-review and pr-review, including signal-selected stack specialists. Load when executing any senior-review workflow or lifecycle review phase.
---

# Unified review method

Input: variant, target/flags, output root; optional same-snapshot `prepared` bundle;
optional `budget` (`delta` for one wave's diff, `full` for the whole candidate) and
`target-kind` (`changeset`, `plan`, `spec`, `doc`), both resolved by preparation
when absent.
Output: native report and the project-result envelope. Do not delegate execution
to a second workflow or a nested lifecycle scheduler. In team-review Phase 1a,
the coordinator executes the canonical `codebase-map:analyze` entry's preflight,
answerable checkpoints, delivery check and publication decision. Its
`codebase-map:map-analyst` runs the requested phases in one isolated context
through this workflow's declared host harness. Loading the method alone executes
no phase; use the analyst as a role, never as a skill or declarative `invoke`.
Keep one review preparation and final report owner; required workers still run
in isolated contexts through the declared host bindings.

The consuming workflow declares the named reviewer inventory in `dispatch.roles`
and isolated inline workers in its sidecar. Any inline lens, critic, history,
hygiene or minimal-fix brief in the references uses the canonical
`project-protocol:isolated-worker` binding supplied by the host harness. Use that
exact binding rather than a generic host role name. Keep scope, authorization,
budget, expected report path and delivered or failed outcome for every brief.

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

Read-only review preserves application files and preexisting edits.
The coordinator alone may perform the project-bound Codebase Map preflight
before dispatch: move an idle legacy archive intact and write only bound
relocation metadata. This bounded exception authorizes no application changes,
analysis run, worker migration or generic filesystem move.
Before any accepted fix, load
`project-protocol:project-protocol` for execution preflight, authorizations,
baseline, candidate gate and owned recovery. Commit and publication are separate
authorizations; a request for review is not authorization to publish.
