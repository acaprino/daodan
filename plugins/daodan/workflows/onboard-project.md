---
description: >
  Explain an unfamiliar project to whoever takes it over: purpose, modules, critical flows, setup and tests, evidenced risks, active decisions, real unknowns and a first scoped work plan. Changes nothing in the project.
  TRIGGER WHEN: the user is new to a project, takes one over, or asks to be walked through it.
  DO NOT TRIGGER WHEN: the user wants a durable guide written into the repository (use write-docs).
argument-hint: "[project or area]"
---

# Onboard onto the project

$ARGUMENTS

Load the skills `project-lifecycle:handover-method` and
`work-controller:work-record` and prepare the consultant dossier of the project or
area named above, or of this project. Depth is standard and no local check runs unless
the user asks for one. Before anything is written, run `run_state.py first-use --project ROOT`; on
`first_use: true`, load `project-lifecycle:lifecycle-method` and follow its
`references/first-use.md` first. Every write stays in the run; maintenance is never started from
here, the dossier names the next step for the user.
