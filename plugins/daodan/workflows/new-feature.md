---
description: >
  Add new behavior through the task cycle: an interview grounded in your code, a proposed decision record, a plan in waves you approve, execution by the stack's specialists with a light review before each commit.
  TRIGGER WHEN: the user wants new behavior, a feature or a capability added; also the default when unsure which work command fits.
  DO NOT TRIGGER WHEN: a defect is to be fixed (use fix-bug) or behavior must stay the same (use refactor-code).
argument-hint: "<what to build>"
---

# New feature

$ARGUMENTS

Load the skills `project-lifecycle:lifecycle-method` and
`project-protocol:project-protocol`. Run operation `change` for the request above
through the phases of the lifecycle method's `references/change.md`, initializing the
project first when it is not in the cycle. A request that turns out to be a defect or a
pure restructuring follows `references/repair.md` or `references/refactor.md` instead,
said to the user. Stop only for the user's answers, the plan approval and the merge
authorization; ask each with the host's question tool, or record it in the run and close
the turn listing it. At the end, propose `/daodan:finish-task`.
