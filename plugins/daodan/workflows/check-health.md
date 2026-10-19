---
description: >
  Diagnose the project's debt without changing it: structure, duplicated concepts, dead code, tests, documentation and instructions, workspace, and each stack's own audit (Python, React, TypeScript, platform, dependencies). Produces a plan of actions with owners and gates.
  TRIGGER WHEN: the user asks how healthy a project is, what its technical debt is, or what to clean up first.
  DO NOT TRIGGER WHEN: one change is to be reviewed (use review-changes or review-branch).
argument-hint: "[area]"
---

# Check the project's health

$ARGUMENTS

Load the skills `project-lifecycle:lifecycle-method` and
`project-protocol:project-protocol`. Run operation `assess`, the diagnosis of the
lifecycle method's `references/assess.md`, with focus `all` on the area named above or
the whole project: knowledge, structure, tests, artifacts and every stack the snapshot
shows. It is read-only. The result is the plan of actions with owner, scope, evidence,
cost and gate, and the command that carries out each one.
