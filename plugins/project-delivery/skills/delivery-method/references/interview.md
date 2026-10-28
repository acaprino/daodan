# Phases 2 and 3: interview and specification

Load `references/specification.md`. Reuse the supplied specification, approval
binding and brainstorm answers. Ask only about missing requirements, conflicts
or changed evidence; do not restart an answered interview.

## Grounding

1. Load `codebase-map:map-method`; deepen through `references/deepen.md`.
   Read cards, `edit-impact` neighbours and current source; cards are leads.
2. Load `project-delivery:adr-method`; `resolve` the scope and inherit the
   relevant active records as constraints.
3. Read base-commit root/nested instructions through `git show <base_sha>:<path>`.
   Record grounding in the run and worker briefs.
4. Before technical claims or acceptance criteria, load
   `research:science-based-approach`, compose its automatic checkpoint and pin
   reused revisions/claims with outcomes. OFF permits no scientific archive or
   network work.

Trace affected callers, tests, fixtures, configuration and exports beyond map
neighbours. Include paths that must change together; locate shared causes.
Agree producer/consumer contracts, wire/error/version compatibility and actual
serialization checks before splitting work. Derive types and mocks.

## Settle and record

Ask through the work record, one question per turn on current/proposed inputs and
outputs. Fix scope/exclusions, nominal/boundary/rejection `EX-*`, rejected `RA-*`,
`INV-*`, affected decisions and execution authorization. Replan before unapproved
paths; keep choices explicit.

Write or revise the project specification and follow its review and approval
contract before planning. The run's `intent.md` links that specification.
Every settled decision follows the capture rule of `project-delivery:adr-method`:
where records are kept, a `Proposed` record reviewed before its own approval,
citing the specification without duplicating its design.

On request, challenge the specification or record through
`peer-review:cross-model-peer-review`, dispatching `peer-review:packet-builder`
and `peer-review:respondent`; bring standoffs to the user. Use
`moe:multi-model-deliberation` for a requested second opinion.
