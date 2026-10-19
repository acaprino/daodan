# Phases 2 and 3: interview and decision record

## Grounding, before the first question

1. Load `codebase-map:map-method`. From the bound run, take the symbol cards of
   the entities the request names and their one-hop callers and callees; read
   the current source of each through the map's source reader. A card is a
   lead; the source is the fact.
2. Load `project-knowledge:adr-method` and run `resolve` on the scope. The
   one to three active records it returns are the constraints the task
   inherits.
3. Read the base-commit instructions (`AGENTS.md`, `CLAUDE.md`, nested files)
   through `git show <base_sha>:<path>`.
4. Record the grounding in the run's `adr` section as `active` and in every
   later worker's brief.

## One question per turn

Ask one question at a time, anchored to a file and line, with the current
and the proposed behavior as concrete input and output from the code or its
tests. Prefer a question that closes a branch of the design. Offer the
recommended answer and what the alternatives cost. Ask through the host's
question tool; when the session has none, write every pending question to
the run's `questions` section, end the turn listing them, and resume on the
same run with the answers.

Stop asking when all of these are fixed:

- scope: paths, modules, domains, symbols, and what is out of scope;
- at least one nominal, one boundary and one rejection example, each as
  input and expected output;
- every alternative the user rejected, with the reason;
- the invariants the code and its tests must keep;
- whether an active record is respected or must be superseded, and by what;
- the authorization: edit, commit, both, or plan only.

Never infer a missing answer: a decision the user did not make stays open in
the record for the plan review to raise again.

## The record

Write the body from the helper's `template`, filling the examples (`EX-*`),
rejected alternatives (`RA-*`) and invariants (`INV-*`) from the answers.
Run `propose` with the title, a slug, the run identity, `base_sha`, the scope
lists and any `--supersedes`. Record the returned identity in the run's `adr`
section as `proposed`. The record stays `Proposed` until integration.

## Review of the record (stage A)

Run `senior-review:review-method` through `senior-review:review-preparation`
with `target-kind=spec` on the record and shape `light`. The preparation
selects the premise lens against the current source, the logic lens for
invariants and missing examples, the abstraction lens against the concept
index, and the stack lenses the scope activates. A `disputed` premise or a
blocking finding reopens the interview on that point.

On `--peer-review`, dispatch `peer-review:packet-builder` and
`peer-review:respondent` through `peer-review:cross-model-peer-review` on the
record; standoffs return to the user as decisions. On `--second-opinion`,
load the `moe:multi-model-deliberation` skill with the record as the brief.
Both are opt-in.
