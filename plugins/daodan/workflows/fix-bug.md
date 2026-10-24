---
description: >
  Fix a defect: first the test that reproduces it, then a short interview, the fix, a light review. A decision record only when the fix changes a contract. Without a known cause, investigates first.
  TRIGGER WHEN: the user reports a bug to fix, a regression or a failing behavior and wants it corrected.
  DO NOT TRIGGER WHEN: the user only wants to understand a problem (use investigate-problem).
argument-hint: "<the defect>"
---

# Fix a bug

$ARGUMENTS

Load the skills `project-lifecycle:lifecycle-method` and
`work-controller:work-record`. Run operation `repair` for the defect above as the
lifecycle method's `references/repair.md` directs: without a demonstrated cause,
`senior-review:investigation-method` runs first and its reproduction test becomes the
oracle. Stop only for the user's answers, the plan approval and the merge authorization;
ask each with the host's question tool, or record it in the run and close the turn
listing it. At the end, propose `/daodan:finish-task`.
