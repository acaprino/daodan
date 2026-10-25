---
description: >
  Bring a project into the Daodan cycle: the first-use choices (decision records, analysis depth), map, decision record index when chosen, verified environment and commands, the loop block in the instructions, the test baseline. On an empty folder, scaffold it first.
  TRIGGER WHEN: a project has never been used with Daodan, or the user asks to set it up or start a new project.
  DO NOT TRIGGER WHEN: the project is already initialized and the user wants work done (use new-feature, fix-bug or refactor-code, which initialize by themselves when needed).
argument-hint: "[what to build, on an empty folder]"
---

# Initialize the project

$ARGUMENTS

Load the skills `project-delivery:delivery-method` and
`work-controller:work-record`.
Before anything is written, run `run_state.py first-use --project ROOT`; on
`first_use: true`, load `project-delivery:delivery-method` and follow its
`references/first-use.md` first. Open a run with operation `assess` and follow the
lifecycle method's `references/init.md`: an empty folder is scaffolded first from what
the user wants to build; an existing project gets the first-use choices, the map at the chosen depth,
the record index when chosen, environment, loop block and test baseline. A part that exists and validates is kept. End
with what was created, what could not be verified, and the command for the first task.
