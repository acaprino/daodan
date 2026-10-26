---
description: >
  Multi-dimensional code, PR and branch review with optional --fix and --commit remediation (including dead-code subtraction).
  TRIGGER WHEN: reviewing recent changes, a PR or a branch for bugs, security or architecture, or removing dead code, unused exports/dependencies and orphan assets.
  DO NOT TRIGGER WHEN: full codebase-wide multi-phase review (use /senior-review:team-review), filesystem/git tidying (use /repo-hygiene:tidy), or readability-only rewrites (use /clean-code:clean-code).
argument-hint: "[PR number | --branch <name> | --commits N] [--fix] [--commit] [--auto-comment] [--strict] [--fast] [--rigorous]"
---

# /senior-review:code-review

Load the `senior-review:review-method` skill and run variant `code-review` with `$ARGUMENTS`.
Resolve this entry's existing target and flags through `senior-review:review-preparation`.
The method owns dispatch, delivery accounting, consolidation and reporting. Keep the
seven native review contracts; operational records use `project-protocol` envelopes.

The same review selects React performance, TypeScript type safety and platform
integration when the target warrants them, alongside testing, structural entropy
and workspace hygiene. Record selected dimensions, skip reasons and coverage gaps
in one review plan and report.
