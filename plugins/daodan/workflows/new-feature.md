---
description: >
  Add new behavior through the task cycle: reuse or write a project specification in docs/specs/, obtain its approval, plan waves and execute through stack specialists with a light review before each commit. ADRs keep separate technical decisions.
  TRIGGER WHEN: the user wants new behavior, a feature or a capability added; also the default when unsure which work command fits.
  DO NOT TRIGGER WHEN: a defect is to be fixed (use fix-bug) or behavior must stay the same (use refactor-code).
argument-hint: "<what to build>"
---

# New feature

$ARGUMENTS

Load the skills `project-delivery:delivery-method` and
`work-controller:work-record`.
Before anything is written, run `run_state.py first-use --project ROOT`; on
`first_use: true`, load `project-delivery:delivery-method` and follow its
`references/first-use.md` first. Run operation `change` for the request above
through the delivery method's `references/change.md`. Reuse supplied specifications
and brainstorm approvals; settle only gaps. Before scaffolding a project without application code,
follow `references/brainstorm.md` through specification approval, then initialize
through `references/init.md`. A request that turns out to be a defect or a
pure restructuring follows `references/repair.md` or `references/refactor.md` instead,
said to the user. Stop only for the user's answers, the plan approval and the merge
authorization; ask each as the work record's question rule says; a yes to an authorization is
also a grant. At the end, propose `/daodan:finish-task`.
