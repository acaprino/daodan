---
description: >
  Write tests for the code you name: behavior-driven, in the project's framework and layout, extending existing files rather than creating parallel ones.
  TRIGGER WHEN: the user asks for tests, more coverage or a test for a specific behavior.
  DO NOT TRIGGER WHEN: a defect is to be fixed with its test (use fix-bug) or the suite is to be audited (use check-health).
argument-hint: "<code or behavior to test>"
---

# Write tests

$ARGUMENTS

Read the argument as a path, a commit, a pull request or a branch when one exists,
otherwise as text, and say how you read it before starting. Load the skills
`testing:test-preparation` and `work-controller:work-record`, prepare the runner
and the layout for the target above, and dispatch `testing:test-writer` in an isolated
context with that preparation. Before anything is written, run `run_state.py first-use --project ROOT`; on
`first_use: true`, load `project-delivery:delivery-method` and follow its
`references/first-use.md` first. Run the new tests with the project's runner and report
them with their output. Committing them is an authorization asked when needed.
