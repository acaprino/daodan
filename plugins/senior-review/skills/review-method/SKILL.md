---
name: review-method
description: >
  Unified review engine: the light review and the branch review (variants team-review and pr-review, and code-review), including signal-selected stack specialists.
  TRIGGER WHEN: the user asks to review current changes, a commit, a file, a plan, a specification, a document, a branch or a pull request for defects, or a host review entry/lifecycle phase runs a review.
  DO NOT TRIGGER WHEN: establishing the root cause of a reported failure without reviewing an artifact (use investigation-method), or removing dead code (use application-cleanup-method).
---

# Unified review method

Input: variant, target/flags, output root; optional same-snapshot `prepared` bundle.
Preparation resolves absent `shape` (`light`/`branch`) and `target-kind`
(`changeset`/`plan`/`spec`/`doc`). Output: native report and project-result envelope.

Before either shape, verify the [Codebase Map prerequisite](../../README.md#prerequisito):
the entire project's map must already be complete.

**Shape `light`:** read only `references/light.md` in this method. Branch uses
`team-review`, or `pr-review` for a pull request, through these steps.

Do not delegate execution to another workflow or nested lifecycle scheduler.
Team-review Phase 1 runs in the coordinator's context with the complete run's
Codebase Map tools; it dispatches nothing and starts no analysis.
Keep one review preparation and final report owner; required workers retain isolation.

The isolated-worker binding is `senior-review:isolated-worker`, five tools and no
host extras: jobs, lenses 1-3, critic, history, hygiene and minimal-fix briefs run
on it. Where the host has not registered it, declare those workers unavailable
and the review incomplete; never substitute the host's generic worker or invent a role.
Dispatch in waves: every worker of one step that depends on no other goes out in a
single turn, and the coordinator waits for that wave's results without spending a
turn per worker. The README section "Esecuzione" gives the reason and an example.
Bind scope, authorization, budget, report path and delivered/failed outcome for
every brief. If no isolated binding exists, declare the missing independence.

1. Load `senior-review:review-preparation`, unless a prepared bundle exists.
   Validate target, run, snapshot, knowledge schema/candidate/fingerprints/scope,
   delivery IDs and applicable activation evidence or skip/gap reason. Reprepare
   stale or incomplete bindings against this candidate, without another run or
   duplicate dispatch.
2. Read `references/<variant>.md`. Dispatch validated `jobs` once each, in one wave, under
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
   Context and verification keep separate inputs and deliveries.
3. Load `senior-review:review-consolidation` with native results. Finish it before
   the variant's output/fix tail.
4. Code review then reads `references/code-review-delivery.md`; team/PR delivery
   stays in consolidation. Execute delivery and authorized fixes once. Application
   subtraction uses `senior-review:application-cleanup-method`; significant semantic
   refactors return to the caller's development plan, never cleanup.

Read-only review preserves application files and preexisting edits.
Before accepted fixes use the host run-record mechanism for preflight,
authorizations, baseline, candidate gate and owned recovery. If it is absent,
declare those gates unavailable. Commit/publication require separate
authorization; review grants neither.
