---
description: >
  Restructure code without changing its behavior: characterization tests first, waves with structural oracles, a review of equivalence. Covers readability too.
  TRIGGER WHEN: the user wants code restructured, simplified, deduplicated, renamed or made more readable with the same behavior.
  DO NOT TRIGGER WHEN: behavior should change (use new-feature or fix-bug).
argument-hint: "<what to restructure>"
---

# Refactor code

$ARGUMENTS

Load the skills `project-lifecycle:lifecycle-method` and
`work-controller:work-record`. Run operation `change` for the request above as the
lifecycle method's `references/refactor.md` directs: characterization tests before any
refactoring wave, structural oracles, behavior unchanged at every step. Stop only for
the user's answers, the plan approval and the merge authorization; ask each as the work record's question rule says; a yes to an authorization is
also a grant. At the end,
propose `/daodan:finish-task`.
