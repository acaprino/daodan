---
description: >
  Auto-detects the scope, runs its analysis dimensions in parallel, and applies fixes with --fix or lands them with --commit. Reuses X-ray context when present.
  TRIGGER WHEN: the user asks for a code review, PR review, branch audit, or a security or architecture pass over recent changes; or asks to find and remove dead code, unused exports, unused dependencies, or orphan assets. For workspace tidying decided by the filesystem and git alone (committed build output, `.gitignore`, scratch directories, git state) use `/repo-hygiene:tidy`.
  DO NOT TRIGGER WHEN: a full multi-phase pipeline is wanted (use /senior-review:team-review) or a single file needs a style pass (use clean-code).
argument-hint: "[PR number | --branch <name> | --commits N] [--fix] [--commit] [--auto-comment] [--strict] [--fast] [--rigorous]"
---

# /senior-review:code-review

Load the `senior-review:review-method` skill and run variant `code-review` with `$ARGUMENTS`.
Resolve this entry's existing target and flags through `senior-review:review-preparation`.
The method owns dispatch, delivery accounting, consolidation and reporting. Keep the
seven native review contracts; operational records use `project-protocol` envelopes.

This universal review includes testing, structural entropy and workspace hygiene.
React performance, TypeScript type safety and platform integration belong to
`/review-plus:code-review`. Include this coverage boundary in the review plan.
