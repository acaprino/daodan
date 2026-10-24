---
description: >
  Complete review of a branch against its base, or of a pull request: every perspective the signals activate, the map, blind derivation of premises and the verification panel, chosen by a script from the diff and the map.
  TRIGGER WHEN: the user asks for a full or deep review of a branch, a pull request or a large change, or before a merge.
  DO NOT TRIGGER WHEN: only the current changes or one commit are to be reviewed (use review-changes).
argument-hint: "[branch or pull request]"
---

# Review the branch

$ARGUMENTS

Load `work-controller:work-record`. Before anything is written, run
`run_state.py first-use --project ROOT`; on `first_use: true`, load
`project-lifecycle:lifecycle-method` and follow its `references/first-use.md`
first. What the user's first-use answers create comes before this command and
is not its write.

Load the skill `senior-review:review-method` with shape `branch` and run variant
`team-review` on the branch above against its base, or on the current branch; a pull
request runs variant `pr-review`. Preparation goes through
`senior-review:review-preparation`, which computes the roster; nothing is dispatched
outside it. The report is read-only; posting comments on a pull request is an
authorization asked when needed.
