---
description: >
  Show where the work stands: open tasks with phase, progress, holder and pending questions, their branches, the map's freshness and the decision records when the project keeps them. Changes nothing.
  TRIGGER WHEN: the user asks what is open, where a task stands, who is working on what, or what to do next.
  DO NOT TRIGGER WHEN: the user wants a task continued (use continue-task).
---

# Show the status

Load the skills `project-lifecycle:lifecycle-method` and
`work-controller:work-record` and follow the lifecycle method's
`references/status.md`. When `run_state.py first-use` returns `first_use: true`,
say that Daodan has not been used on this project, name `/daodan:init-project`
and stop. It reads only: no run is opened and nothing is written.
