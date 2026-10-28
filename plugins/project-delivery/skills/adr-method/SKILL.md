---
name: adr-method
description: >
  Create, resolve, validate, approve, version and verify canonical architecture decision records in docs/adr/.
  TRIGGER WHEN: the user explicitly asks to record or write down an architecture or technical decision, a brainstorming or interview settles a product, feature, design, contract or domain decision, whatever brainstorming method runs, a task needs the decisions governing its scope, the user approves, revises or abandons a record, or a reviewed change verifies records or lists their drift.
  DO NOT TRIGGER WHEN: the conversation settles no decision, the change needs no decision beyond existing records, or the request is project documentation (use project-knowledge:project-knowledge).
---

# Architecture decision records

Inside a Daodan run, load the skill `work-controller:work-record`. The helper is
`python "${CLAUDE_PLUGIN_ROOT}/skills/adr-method/scripts/adr_tool.py"`.

## Load map

| Step | Run |
|---|---|
| Before relying on records | `validate --project ROOT`; `--sha HEAD_SHA` for status, realignment |
| Settled decision | `state --project ROOT`; `decline` on a no |
| Before an interview | `resolve --project ROOT --paths P... --modules M... --domains D... --symbols S...` |
| Writing a record or a version | read `references/adr-template.md`; `template`, then `propose` |
| The user approved the text shown | `promote --adr ADR-NNNN --sha HEAD_SHA --expect-digest D` |
| Code reviewed as conforming | `verify --adr ADR-NNNN --sha SHA --expect-digest D` |

## Resolve

Load the one to three most specific `Accepted` matches, never the whole
directory.

## Capture

Every decision a product or feature brainstorming (any method) or an interview
settles follows `state`, never duplicating the specification's design:

- `active`: propose it into `docs/adr/` (`init-index` first if unindexed);
  `foreign` records are read-only constraints.
- `undecided`: ask once whether records become this project's method, yes by
  default. Yes: `init-index`, commit the index alone if a commit exists,
  propose. No: `decline`; say `/daodan:record-decision` turns records back on.
- `declined`: nothing unless the user asks; `/daodan:record-decision` then
  turns records on.

## Propose

Once scope, at least one agreed example, alternatives and invariants are fixed,
write the body and `propose` with title, slug, `--task` (run identity or
brainstorm slug), `--sha` (resolved `HEAD`, omitted only before a first commit,
here and in `promote`), scope lists (never empty; domains suffice before code)
and optional `--supersedes`/`--depends-on`. A refusal names the fix; never
hand-edit the index. `propose --revise ADR-NNNN` writes the next `Proposed`
version under that number. `ADR-NNNN` cites the active version; `ADR-NNNN vN`
pins one.

Versions: at most one `Accepted` and one `Proposed` version per decision.

## Approve, retire, verify

`Accepted` means the user approved this exact text. Show the record and digest,
then `promote`. Record `dependents_to_review` with `ask`. Approval authorizes no
work or merge. Unapproved records stay `Proposed`; abandon with
`retire --adr ADR-NNNN --reason TEXT --expect-digest D`; never delete.
A mismatched `--expect-digest` refuses the rewrite: show the record again.

`verify` sets `last_verified_sha`; approval never verifies. `validate --sha`
lists as `drifted` each `Accepted` record whose governed files changed since,
`files: null` when never verified.

## Instructions and documentation

Durable instructions carry the active records for a domain inside the loop
block that `project-knowledge:instructions-method` maintains; guides cite a
record by identity and never restate its examples.
