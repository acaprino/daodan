---
description: >
  Bring a project into the Daodan cycle: map, decision record index, verified environment and commands, the loop block in the instructions, the test baseline. On an empty folder, scaffold it first.
  TRIGGER WHEN: a project has never been used with Daodan, or the user asks to set it up or start a new project.
  DO NOT TRIGGER WHEN: the project is already initialized and the user wants work done (use new-feature, fix-bug or refactor-code, which initialize by themselves when needed).
argument-hint: "[what to build, on an empty folder]"
---

# Initialize the project

$ARGUMENTS

Load the skills `project-lifecycle:lifecycle-method` and
`project-protocol:project-protocol`. Open a run with operation `assess` and follow the
lifecycle method's `references/init.md`: an empty folder is scaffolded first from what
the user wants to build; an existing project gets its lite map, record index,
environment, loop block and test baseline. A part that exists and validates is kept. End
with what was created, what could not be verified, and the command for the first task.
