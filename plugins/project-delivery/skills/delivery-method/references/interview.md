# Phases 2 and 3: interview and specification

Load `references/specification.md`. Reuse the supplied specification, approval
binding and brainstorm answers. Ask only about missing requirements, conflicts
or changed evidence; do not restart an answered interview.

## Grounding

1. Load `codebase-map:map-method`; deepen through `references/deepen.md`.
   Read cards, `edit-impact` neighbours and current source; cards are leads.
2. With decision records, load `project-delivery:adr-method`; `resolve` the
   scope and inherit the relevant active records as constraints.
3. Read base-commit root/nested instructions through `git show <base_sha>:<path>`.
   Record grounding in the run and worker briefs.
4. Before settling technical claims or specification acceptance criteria, load
   `research:science-based-approach` and compose its automatic checkpoint with
   the caller task, phase and semantic context. Preserve the outcome and pin
   reused research revisions/claims; OFF grants no scientific archive or
   network work.

Trace affected callers, tests, fixtures, configuration and exports beyond map
neighbours. Include paths that must change together; locate shared causes.
Agree producer/consumer contracts, wire/error/version compatibility and actual
serialization checks before splitting work. Derive types and mocks.

## Settle and record

Ask through the work record, one question per turn, grounded in concrete
current/proposed inputs and outputs. Fix scope/exclusions, nominal/boundary/rejection
`EX-*`, rejected `RA-*`, `INV-*`, affected decisions and execution authorization.
Replan before editing unapproved paths. Open choices remain explicit.

Write or revise the project specification and follow its review and approval
contract before planning. The run's `intent.md` links that specification.
When a separate technical decision needs an ADR, use `template` and `propose`
(or `--revise`), review it, then obtain approval of its own digest before
`promote`; record `dependents_to_review` with `ask`. Unapproved records stay
`Proposed`. Do not duplicate the full design into an ADR.

On request, challenge the specification or record through
`peer-review:cross-model-peer-review`, dispatching `peer-review:packet-builder`
and `peer-review:respondent`; bring standoffs to the user. Use
`moe:multi-model-deliberation` for a requested second opinion.
