---
description: >
  Bring a project into the Daodan cycle: the first-use analysis depth, map, verified environment and commands, the loop block in the instructions, the test baseline. Without application code, obtain specification approval before scaffolding.
  TRIGGER WHEN: a project has never been used with Daodan, or the user asks to set it up or start a new project.
  DO NOT TRIGGER WHEN: the project is already initialized and the user wants work done (use new-feature, fix-bug or refactor-code, which initialize by themselves when needed).
argument-hint: "[what to build, without application code]"
---

# Initialize the project

$ARGUMENTS

Load the skills `project-delivery:delivery-method` and
`work-controller:work-record`.
Before anything is written, run `run_state.py first-use --project ROOT`; on
`first_use: true`, load `project-delivery:delivery-method` and follow its
`references/first-use.md` first. Open a run with operation `assess` and follow the
delivery method's `references/init.md`. For projects without application code,
obtain or verify the approved specification before any scaffolder; existing valid
approval and answered questions are reused. The shared initialization method owns
this prerequisite for every caller. Return to initialization after approval;
starting a feature requires its own authorization. Existing projects retain valid
parts and get the chosen map, environment, instruction loop
block and baseline. Report created parts, unavailable checks and the first task.
