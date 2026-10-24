# Phases 2 and 3: interview and decision record

## Grounding before questions

1. Load `codebase-map:map-method`; deepen the requested area using
   `references/deepen.md`. Read entity cards, `edit-impact` one-hop neighbours and current source;
   cards are leads, source establishes facts.
2. Load `project-knowledge:adr-method`; `resolve` the scope. Inherit the
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

Ask one question at a time, anchored to a file/line and concrete current/proposed
inputs and outputs. Close design branches; recommend an answer and explain costs.
Use the host's question tool; without one, record every pending question in the
run's `questions` section, end the turn listing them, and resume that run with
answers.

Stop when these are fixed:

- scope: paths, modules, domains, symbols and exclusions;
- at least one nominal, one boundary and one rejection example, each with
  input and expected output;
- every alternative the user rejected, with its reason;
- code and test invariants;
- active records respected or superseded, and their replacements;
- authorization: edit, commit, both or plan only.

Never infer missing answers: undecided questions stay open in the record for
plan review to raise again.

## The record

Fill the helper's `template` with answered examples (`EX-*`), rejected
alternatives (`RA-*`) and invariants (`INV-*`). Run `propose` with title, slug,
run identity, `base_sha`, scope lists and any `--supersedes`. Save the returned
identity as `proposed` in the run's `adr` section. Keep the record `Proposed`
until integration.

## Record review (stage A)

Run `senior-review:review-method` on the record: shape `light`, kind `spec`, stage `record`.
The premise auditor checks every code claim and missing boundary or rejection
examples. False claims or blocking findings reopen that interview point.

Only on request, challenge the record through `peer-review:cross-model-peer-review`,
dispatching `peer-review:packet-builder` and `peer-review:respondent`; return
standoffs to the user. For a requested second opinion, load
`moe:multi-model-deliberation` on the record.
