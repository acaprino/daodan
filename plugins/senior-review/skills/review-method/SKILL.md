---
name: review-method
description: >
  Unified review engine: the light review and the branch review (variants team-review and pr-review, and code-review), including signal-selected stack specialists.
  TRIGGER WHEN: the user asks to review current changes, a commit, a file, a plan, a specification, a document, a branch or a pull request for defects, or /daodan:review-changes, /daodan:review-branch or a lifecycle review phase runs a review.
  DO NOT TRIGGER WHEN: establishing the root cause of a reported failure without reviewing an artifact (use investigation-method), or removing dead code (use application-cleanup-method).
---

# Unified review method

Input: variant, target/flags, output root; optional same-snapshot `prepared` bundle.
Preparation resolves absent `shape` (`light`/`branch`) and `target-kind`
(`changeset`/`plan`/`spec`/`doc`). Output: native report and project-result envelope.

**Shape `light`:** read only `references/light.md` in this method. Branch uses
`team-review`, or `pr-review` for a pull request, through these steps.

Do not delegate execution to another workflow or nested lifecycle scheduler.
For team-review Phase 1a, the coordinator executes `codebase-map:map-method`
analyze preflight, answerable checkpoints, delivery check and publication decision.
Its `codebase-map:map-analyst` executes requested phases in one isolated context
through the declared host harness. Loading a method executes no phase; the analyst
is a role, never a skill or declarative `invoke`.
Keep one review preparation and final report owner; required workers retain isolation.

The workflow sidecar declares `dispatch.roles` and isolated inline workers.
Inline lens, critic, history, hygiene and minimal-fix briefs use
`work-controller:isolated-worker` through that host binding, never an invented
generic role. Bind scope, authorization, budget, report path and delivered/failed
outcome for every brief.

1. Load `senior-review:review-preparation`, unless a prepared bundle exists.
   Validate target, run, snapshot, knowledge schema/candidate/fingerprints/scope,
   delivery IDs and applicable activation evidence or skip/gap reason. Reprepare
   stale or incomplete bindings against this candidate, without another run or
   duplicate dispatch.
2. Read `references/<variant>.md`. Dispatch validated `jobs` once each under
   preparation's `references/composition.md`, including stack members. The roster
   supplies coverage obligations, never another dispatch list. Core inputs remain
   canonical in `senior-review:review-quality-gates`; stack members use their
   provider definitions and shared preparation. Preserve `knowledge_selection`;
   assign scoped `knowledge_ids`, fingerprint and exact catalog load/reference
   bindings. Workers read assigned knowledge, apply it against source and return
   `knowledge_usage` with scope, worker, hashes, references and application evidence.
   Account for knowledge lenses in the same ledger.
   No worker receives peer findings before delivery.
   Use isolated contexts and the host's coordination mechanism.
   Account for every selected worker before starting consolidation.
   Each member retains canonical checks, coverage and finding references.
   Context, blind derivation and verification keep separate inputs and deliveries.
3. Load `senior-review:review-consolidation` with native results. Finish it before
   the variant's output/fix tail.
4. Code review then reads `references/code-review-delivery.md`; team/PR delivery
   stays in consolidation. Execute delivery and authorized fixes once. Application
   subtraction uses `senior-review:application-cleanup-method`; significant semantic
   refactors return to the caller's development plan, never cleanup.

Read-only review preserves application files and preexisting edits.
Before accepted fixes load `work-controller:work-record` for preflight,
authorizations, baseline, candidate gate and owned recovery. Commit/publication
require separate authorization; review grants neither.
