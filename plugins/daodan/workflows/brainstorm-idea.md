---
description: >
  Guide an idea into a project specification in docs/specs/: clarify intent, compare approaches, write the design and obtain approval before planning. Reuse supplied specifications and answers. Writes no code.
  TRIGGER WHEN: the user wants brainstorming, project design or specifications, or an idea needs clarification before building it; no explicit command is required.
  DO NOT TRIGGER WHEN: the request is already clear enough to build (use new-feature).
argument-hint: "<idea>"
---

# Brainstorm an idea

$ARGUMENTS

Load the skills `project-delivery:delivery-method` and
`work-controller:work-record` and follow the delivery method's
`references/brainstorm.md` with the idea above.
Before anything is written, run `run_state.py first-use --project ROOT`; on
`first_use: true`, load `project-delivery:delivery-method` and follow its
`references/first-use.md` first. Carry the approved specification's path, digest,
approval source and answered questions into the new-feature method when the user
authorizes building. Continue that method here; do not restart the interview or
invoke a competing brainstorming/planning workflow.
