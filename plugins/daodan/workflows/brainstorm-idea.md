---
description: >
  Explore an idea with the user, grounded in the code and, when the project keeps them, its decision records: one question at a time, alternatives with their costs. Writes no code. Ends by starting the feature, keeping a note in docs/ideas/, or dropping it.
  TRIGGER WHEN: the user has an idea that is not yet clear, or wants to think something through before building it.
  DO NOT TRIGGER WHEN: the request is already clear enough to build (use new-feature).
argument-hint: "<idea>"
---

# Brainstorm an idea

$ARGUMENTS

Load the skills `project-lifecycle:lifecycle-method` and
`work-controller:work-record` and follow the lifecycle method's
`references/brainstorm.md` with the idea above.
Before anything is written, run `run_state.py first-use --project ROOT`; on
`first_use: true`, load `project-lifecycle:lifecycle-method` and follow its
`references/first-use.md` first. When the user chooses to build it,
continue as `/daodan:new-feature` with the brief the brainstorm wrote, so the interview
starts from it.
