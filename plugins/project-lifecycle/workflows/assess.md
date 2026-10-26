---
description: >
  Assess project coherence and produce a scoped evidence-based repair plan.
  TRIGGER WHEN: the user requests lifecycle assess or its complete project outcome.
  DO NOT TRIGGER WHEN: a single-domain audit suffices (use /senior-review:code-review, /codebase-map:analyze, or /testing:test-audit).
argument-hint: "[target] [--focus=all|knowledge|structure|tests|artifacts] [--depth=quick|standard|deep] [--run-id ID] [--out INTERNAL_ROOT] [--dry-run|--fix|--commit]"
---

# Assess

$ARGUMENTS

Load the skills project-lifecycle:lifecycle-method and project-protocol:project-protocol.
Perform the assess reference in this coordinator context. Preserve exact run identity,
scope, input snapshots, existing authorization and native specialist boundaries.
Write the common result with coverage, deliveries, checks and unresolved limits.

