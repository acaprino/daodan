---
description: >
  Resume the current branch's task, from this session or another: answers pending questions with the text given, then continues from the first open step.
  TRIGGER WHEN: the user wants to go on with an interrupted task, answers questions a command left pending, or opens a new session on a task branch.
  DO NOT TRIGGER WHEN: no task exists on this branch and the user wants new work (use new-feature, fix-bug or refactor-code).
argument-hint: "[answers]"
---

# Continue the task

$ARGUMENTS

Load the skills `project-lifecycle:lifecycle-method` and
`work-controller:work-record` and follow the lifecycle method's
`references/continue.md`. The text above, when given, answers the pending questions in
order. Stop only for the user's answers, the plan approval and the merge authorization;
ask each with the host's question tool, or record it in the run and close the turn
listing it. At the end, propose `/daodan:finish-task`.
