---
description: >
  Record an architecture decision outside a task: a grounded interview, then a Proposed record under docs/adr/ and its index.
  TRIGGER WHEN: the user wants to write down, propose or document a technical decision.
  DO NOT TRIGGER WHEN: the decision belongs to a task being built (new-feature records it).
argument-hint: "<decision>"
---

# Record a decision

$ARGUMENTS

Load the skills `project-knowledge:adr-method` and `work-controller:work-record`.
Open a run with operation `change` and the decision above as its objective; run
`validate`, then `resolve` on the scope the decision governs. Conduct the grounded
interview, one question per turn anchored to a file and line, until scope, examples,
rejected alternatives and invariants are fixed; then write the body and run `propose`.
The record stays `Proposed` until a task implements it.
