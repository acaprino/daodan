---
description: >
  Record an architecture decision outside a task: a grounded interview, a Proposed record under docs/adr/ and its index, then your approval, which accepts it without waiting for code. On a project without decision records, this turns them on.
  TRIGGER WHEN: the user wants to write down, propose, revise or document a technical decision.
  DO NOT TRIGGER WHEN: the decision belongs to a task being built (new-feature records it).
argument-hint: "<decision>"
---

# Record a decision

$ARGUMENTS

Load the skills `project-delivery:adr-method` and `work-controller:work-record`.
Before anything is written, run `run_state.py first-use --project ROOT`; on
`first_use: true`, load `project-delivery:delivery-method` and follow its
`references/first-use.md` first. This command
implies yes to decision records, so it asks only about the analysis. On a project
without `docs/adr/README.md`, run `init-index` and say that the project now keeps
decision records.
Open a run with operation `change` and the decision above as its objective; run
`validate`, then `resolve` on the scope the decision governs. Conduct the grounded
interview, one question per turn anchored to a file and line, until scope, examples,
rejected alternatives and invariants are fixed; then write the body and run `propose`,
with `--revise ADR-NNNN` when the decision changes an `Accepted` one.
Show the record with its `digest` and ask the user to approve that text. On approval,
run `promote` with the current `HEAD` and `--expect-digest`, without waiting for code,
and record each `dependents_to_review` entry as an open question with `ask`. Say that
the approval created no task and authorized no edit, commit or merge. A record the
user does not approve stays `Proposed`; one the user abandons is retired with `retire`.
