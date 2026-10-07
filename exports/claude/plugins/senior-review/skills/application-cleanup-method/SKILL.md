---
name: application-cleanup-method
description: >
  Apply accepted application-subtraction findings with isolated phases and snapshot-bound build/test gates.
---

# Application cleanup

Input: accepted cleanup findings and severities, target, explicit scope, output
root, exclusively owned isolated workspace, clean tree, targeted-fix delivery,
commit authorization and required build/test commands. Output: phase ledger with
pre-phase SHA, candidate snapshot, gate evidence, commit or verified recovery.

Load the `project-protocol:project-protocol` skill for execution preflight and the canonical
gate/recovery procedure. Reuse recorded authorization; ask only for missing choices.
Read `references/application-cleanup.md` inside this skill. Its subtraction method
is promoted from Step 7c without adding a new auditor or a semantic refactor engine.
Inputs can come from a review or an identified lifecycle plan. When targeted fixes
were unnecessary, record 7b as not applicable; otherwise its accepted changes must
be delivered and committed before subtraction. Plain `--fix` leaves
this commit-only action open and explains the missing capability before execution.
