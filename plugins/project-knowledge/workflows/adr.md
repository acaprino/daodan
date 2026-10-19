---
description: >
  Create, resolve, validate or promote architecture decision records in docs/adr/.
  TRIGGER WHEN: the user asks which decisions govern a scope, wants a decision recorded after an interview, or merged a change that implements a Proposed record.
  DO NOT TRIGGER WHEN: the user wants a decision challenged (use /senior-review:code-review on the record, or /peer-review:review).
argument-hint: "resolve <paths...> | propose --title T --slug S [--supersedes ADR-NNNN] | validate [ADR-NNNN] | promote ADR-NNNN --sha SHA | init"
---

# ADR

Load `project-knowledge:adr-method` and execute the requested operation for
`$ARGUMENTS` with its helper. Reuse a caller's owned run and authorizations;
otherwise initialize one through `project-protocol:project-protocol` with
operation `change` and the record as its objective.

`resolve` and `validate` read only. `init` creates the index. `propose` writes
one new `Proposed` record and the index: conduct the grounded interview in this
context first, one question per turn anchored to a file and line, until scope,
examples, rejected alternatives and invariants are fixed; then write the body
and run the helper. `promote` needs the merged commit sha and a run whose
required gates passed on that commit; it is the only way a record becomes
`Accepted`.

Record the helper's JSON output in the run. A refusal is reported verbatim and
leaves the directory unchanged. Commit only when authorized.
