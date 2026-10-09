---
description: >
  Prepare an evidence-based consultant intake dossier without changing the project.
  TRIGGER WHEN: the user requests lifecycle handover or needs to take responsibility for an unfamiliar project.
  DO NOT TRIGGER WHEN: the user requests correction and rationalization (use maintain).
argument-hint: "[target] [--depth=quick|standard|deep] [--checks=none|local] [--run-id ID] [--out INTERNAL_ROOT]"
---

# Handover

$ARGUMENTS

Load project-lifecycle:handover-method and project-protocol:project-protocol.
Prepare the consultant dossier through the canonical project-knowledge methods in
this coordinator context. Default to depth standard and checks none. Keep every
write inside the identified run and every check within its recorded authorization.
Preserve exact scope, snapshots, native deliveries and evidence limitations.
Do not start maintenance; the dossier identifies a possible next step for the user.
