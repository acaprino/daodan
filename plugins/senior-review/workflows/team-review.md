---
description: >
  Six-phase pipeline. Builds X-ray and interconnect context first, then runs specialized dimensions in parallel so cross-component logic bugs surface, not just local ones.
  TRIGGER WHEN: the user wants a multi-reviewer review of a whole codebase or a large change, or asks for the deepest review available.
argument-hint: "<target> [--reviewers auto|security,performance,react,typescript,platform,...] [--base-branch main] [--all] [--deep] [--no-context] [--fast] [--rigorous]"
---

# /senior-review:team-review

Load the `senior-review:review-method` skill and run variant `team-review` with `$ARGUMENTS`.
Resolve this entry's existing target and flags through `senior-review:review-preparation`.
The method owns dispatch, delivery accounting, consolidation and reporting. Keep the
seven native review contracts; operational records use `project-protocol` envelopes.

The same review selects React performance, TypeScript type safety and platform
integration when the target warrants them, alongside testing, structural entropy
and workspace hygiene. Record selected dimensions, skip reasons and coverage gaps
in one review plan and report.
