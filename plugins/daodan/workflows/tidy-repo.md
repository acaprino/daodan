---
description: >
  Clean the repository: workspace garbage and git leftovers, dead application code, redundant tests, concluded run output. Preview first, then one authorization.
  TRIGGER WHEN: the user asks to clean up, tidy, remove dead code, junk files or redundant tests.
  DO NOT TRIGGER WHEN: the code itself is to be restructured (use refactor-code).
argument-hint: "[area]"
---

# Tidy the repository

$ARGUMENTS

Load `work-controller:work-record` and preview, on the area above or the whole
project, each owner's detection:

| What | Method |
|---|---|
| filesystem garbage, tracked build output, git leftovers | `repo-hygiene:repo-hygiene`, its `references/tidy.md` |
| dead code, orphan assets, unused dependencies | `senior-review:application-cleanup-method` |
| redundant or obsolete tests | `testing:test-remediation-method`, mode `consolidate` |
| output of concluded Daodan runs | `project-delivery:delivery-method`, its `references/retention.md` |

Before anything is written, run `run_state.py first-use --project ROOT`; on
`first_use: true`, load `project-delivery:delivery-method` and follow its
`references/first-use.md` first.
Show one preview, then ask once which groups to apply and whether to commit. Untracked
removals are quarantined, never deleted; permanent deletion is a separate authorization.
