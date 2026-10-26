---
description: >
  Generates a risk assessment, a review checklist, and a lite dead-code and VCS-hygiene pass over the diff, then submits it via gh with --create.
  TRIGGER WHEN: the user asks to prepare a PR, write a PR description, or open a pull request from the current branch.
  DO NOT TRIGGER WHEN: reviewing someone else's PR (use /senior-review:code-review with the PR number).
argument-hint: "[--base main] [--create] [--split-check] [--strict-mode]"
---

# /senior-review:pr-review

Load the `senior-review:review-method` skill and run variant `pr-review` with `$ARGUMENTS`.
Resolve this entry's existing target and flags through `senior-review:review-preparation`.
The method owns dispatch, delivery accounting, consolidation and reporting. Keep the
seven native review contracts; operational records use `project-protocol` envelopes.

The same PR assessment selects React performance, TypeScript type safety and
platform integration when the target warrants them. Their findings and coverage
gaps enter the native risk assessment and PR description through one consolidation.
