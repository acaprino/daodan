# Phases 2 and 3: interview and decision record

## Grounding before questions

1. Load `codebase-map:map-method`; deepen the requested area using
   `references/deepen.md`. Read entity cards, `edit-impact` one-hop neighbours and current source;
   cards are leads, source establishes facts.
2. Load `project-delivery:adr-method`; `resolve` the scope. Inherit the
   returned one to three active records as constraints.
3. Read base-commit instructions (`AGENTS.md`, `CLAUDE.md`, nested files)
   through `git show <base_sha>:<path>`.
4. Record grounding as `active` in the run's `adr` section and every later
   worker brief.

Before fixing scope, trace affected callers, tests, fixtures, configuration and
exports beyond map neighbours. Include paths that must change together; locate
bugs’ shared cause before choosing repairs. Replan before editing unapproved paths.
Before splitting producer/consumer work, agree the authoritative contract and
wire/error/version compatibility. Derive types/mocks; check actual serialization.
A shared type suffices within an atomic boundary; schema validity proves no domain rule.

## One question per turn

Ask as the work record's question rule says, anchored to a file/line and
concrete current/proposed inputs and outputs. Close design branches.

Stop when these are fixed:

- scope: paths, modules, domains, symbols and exclusions;
- at least one nominal, one boundary and one rejection example, each with
  input and expected output;
- every alternative the user rejected, with its reason;
- code and test invariants;
- active records respected, revised or superseded;
- authorization: edit, commit, both or plan only.

Undecided questions stay open in the record for plan review.

## The record

Fill the helper's `template` with answered examples (`EX-*`), rejected
alternatives (`RA-*`) and invariants (`INV-*`). Run `propose` at `base_sha`,
`--revise` to change an active decision; its id is `adr.proposed`. Without
records, it is the run's `intent.md`.

## Review (stage A) and approval

Run `senior-review:review-method` on the record: shape `light`, kind `spec`, stage `record`.
False claims or blocking findings reopen that interview point.

On request only, challenge the record through `peer-review:cross-model-peer-review`,
dispatching `peer-review:packet-builder` and `peer-review:respondent`, standoffs
to the user, or load `moe:multi-model-deliberation` for a second opinion.

With records, show the record and its `digest` and ask the user to approve it;
on approval, `promote` it at `HEAD`, recording each `dependents_to_review` with
`ask`. Unapproved, it stays `Proposed`.
