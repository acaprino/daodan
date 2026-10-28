---
description: >
  Show where the work stands: open tasks with phase, progress, holder and pending questions, their branches, the map's freshness and the decision records when the project keeps them. Changes nothing.
  TRIGGER WHEN: the user asks what is open, where a task stands, who is working on what, or what to do next.
  DO NOT TRIGGER WHEN: the user wants a task continued (use continue-task).
---

# Show the status

Load the skills `project-delivery:delivery-method` and
`work-controller:work-record` and follow the lifecycle method's
`references/status.md`. When `run_state.py first-use` returns `first_use: true`,
say that Daodan has not been used on this project and name `/daodan:init-project`.
A brainstorm captures decision records without a run, so when `adr_tool.py state`
of `project-delivery:adr-method` reports `active`, also list the records as step 4
of `references/status.md` does (`validate` without `--sha` before the first
commit) and the `foreign` directories `state` names. Then stop. It reads only:
no run is opened and nothing is written.
