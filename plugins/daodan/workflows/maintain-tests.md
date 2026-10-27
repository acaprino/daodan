---
description: >
  Maintain an existing test suite: review protection, update outdated checks, consolidate duplicates and reorganize ownership, with accepted scope and verified protection.
  TRIGGER WHEN: the user asks to clean up, rationalize, consolidate, reorganize or revise existing tests.
  DO NOT TRIGGER WHEN: only adding protection for a behavior (use write-tests) or fixing a product defect (use fix-bug).
argument-hint: "<suite, module or maintenance objective>"
---

# Maintain tests

$ARGUMENTS

Load `work-controller:work-record`, `testing:test-preparation` and
`testing:test-remediation-method`. Resolve the requested suite or module and
reuse preparation only for that scope and snapshot. Before any write, run
`run_state.py first-use --project ROOT`; on `first_use: true`, load
`project-delivery:delivery-method` and follow `references/first-use.md` first.
Declare the native `test-consolidate-report` delivery at
`<output-root>/consolidation.md`, owned by the coordinator.

Follow the canonical consolidation method in dry-run first, producing its
behavior/failure-mode inventory and proposed reuse, update, consolidation or
retirement. Use its audit mode only when diagnosis or the requested scope needs
it. Keep static findings and unavailable runtime evidence explicit.

Apply only accepted actions, reusing an earlier grant that already covers them;
unanswered inventory rows stay protected. Resume from the accepted inventory
without a second detection pass. The method classifies failures and routes
test repairs to `testing:test-writer` in an isolated context; product and
environment defects retain their proper owners. Preserve independent failure
modes, oracles and bugfix provenance. Bind required checks to the actual
candidate and deliver the canonical report with retained protection and open
actions. The coordinator verifies every required delivery before closure.
