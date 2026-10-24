---
description: >
  Investigate an error, a bug or a strange behavior without fixing it: facts, perimeter from the map, hypotheses verified one by one in isolation, a reproduction test, bisection. Ends with the demonstrated cause or the remaining hypotheses and what would decide them.
  TRIGGER WHEN: the user reports an error, a failure, a regression or behavior they cannot explain, and the cause is not known.
  DO NOT TRIGGER WHEN: the cause is known and a fix is wanted (use fix-bug).
argument-hint: "<error, symptom or failing command>"
---

# Investigate a problem

$ARGUMENTS

Read the argument as a path, a commit, a pull request or a branch when one exists,
otherwise as text, and say how you read it before starting. Load the skills
`senior-review:investigation-method` and `work-controller:work-record` and
investigate the problem above. Nothing in the product changes; the reproduction test is
the one project file it writes, uncommitted. When the user wants it fixed, continue as
`/daodan:fix-bug` with the reproduction test as its oracle.
