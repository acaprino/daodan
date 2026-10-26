---
description: >
  List all project worktrees, add concise descriptions and tags, create or resume
  a task workspace, and check Worktrunk upstream compatibility.
  TRIGGER WHEN: the user asks to list, describe, tag or manage task worktrees,
  or update the Worktrunk engine.
  DO NOT TRIGGER WHEN: starting a feature or finishing a task; those entries
  compose the same workspace method within their existing delivery cycle.
argument-hint: "[request]"
---

# Manage worktrees

$ARGUMENTS

Load skills `worktree-manager:worktree-method` and `work-controller:work-record`.
Without a specific request, show the read-only inventory, including external and
detached checkouts. Apply requested descriptions and tags to the identified
workspace; ambiguity is resolved before changing an annotation. Creation uses
the task's existing identity, authorization and workspace policy. Final review,
merge and completion load skill `project-delivery:delivery-method`, following
its `references/finish.md`; this entry never bypasses those gates.
Dispatch only the workers that the selected method requires. Inventory and
annotation do not start review workers or a delivery cycle. An explicit finish
request uses this entry's declared isolated worker bindings and the existing
delivery owner, including its review and realignment barriers.
