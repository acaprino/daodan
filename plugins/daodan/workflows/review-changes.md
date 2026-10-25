---
description: >
  Light review of the current changes, the last commit, or the file, folder or commit you name: the project's tools, then one reviewer chosen by the target's kind. Code, plans, specifications and documents. Read-only.
  TRIGGER WHEN: the user asks to review their changes, a commit, a file or a document.
  DO NOT TRIGGER WHEN: a whole branch or a pull request is to be reviewed (use review-branch).
argument-hint: "[file, folder or commit]"
---

# Review the changes

$ARGUMENTS

Load `work-controller:work-record`. Before anything is written, run
`run_state.py first-use --project ROOT`; on `first_use: true`, load
`project-lifecycle:lifecycle-method` and follow its `references/first-use.md`
first.

Load the skill `senior-review:review-method` with shape `light` and follow its
`references/light.md` on the target above. The roster is the helper's; when it advises a
branch review, say so and stop rather than widen. Findings are reported, never fixed.
