---
description: >
  Verify an exact candidate snapshot and account for checks, coverage and remaining gaps.
  TRIGGER WHEN: the user requests lifecycle verify or its complete project outcome.
  DO NOT TRIGGER WHEN: a narrower specialist task already covers the requested outcome.
argument-hint: "[target] [--focus=all|knowledge|structure|tests|artifacts] [--depth=quick|standard|deep] [--run-id ID] [--out INTERNAL_ROOT] [--dry-run|--fix|--commit]"
---

# Verify

$ARGUMENTS

Load the skills project-lifecycle:lifecycle-method and project-protocol:project-protocol.
Perform the verify reference in this coordinator context. Preserve exact run identity,
scope, input snapshots, existing authorization and native specialist boundaries.
Write the common result with coverage, deliveries, checks and unresolved limits.

