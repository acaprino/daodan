---
description: >
  Run the complete guided maintenance campaign: orientation, stage-by-stage repair of knowledge, structure, tests and artifacts, each stage approved before the next, final verification.
  TRIGGER WHEN: the user wants a whole project brought back into good shape over several stages.
  DO NOT TRIGGER WHEN: one diagnosis is enough (use check-health) or one change is wanted (use new-feature, fix-bug or refactor-code).
argument-hint: "[area]"
---

# Run the maintenance campaign

$ARGUMENTS

Load the skills `project-lifecycle:maintainer-method` and
`work-controller:work-record` and coordinate the campaign on the area named above
or the whole project: separate lifecycle runs and explicit stage handoffs, guided
checkpoints, deep depth. Before anything is written, run `run_state.py first-use --project ROOT`; on
`first_use: true`, load `project-lifecycle:lifecycle-method` and follow its
`references/first-use.md` first. Every stage is a preview until the user authorizes its edits at
the step that needs them. Report complete only from validated stage results and a final
verification against the current project.
