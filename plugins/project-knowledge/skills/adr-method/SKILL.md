---
name: adr-method
description: >
  Create, resolve, validate and promote canonical architecture decision records in docs/adr/.
  TRIGGER WHEN: the user explicitly asks to record or write down an architecture or technical decision, an interview settles a design, contract or domain decision, a task needs the decisions governing its scope, or a merged change promotes a Proposed record.
  DO NOT TRIGGER WHEN: the user only wants brainstorming or advice without recording a decision, the change needs no decision beyond existing records, or the request is project documentation (use project-knowledge:project-knowledge).
---

# Architecture decision records

Load the skill `project-protocol:project-protocol` for run ownership and authorization.
The helper is `python "${CLAUDE_PLUGIN_ROOT}/skills/adr-method/scripts/adr_tool.py"`;
it writes records and the index atomically and refuses an inconsistent state
first. The record format is `references/adr-template.md`.

## Load map

| Step | Read | Run |
|---|---|---|
| Any | this file | `validate --project ROOT` before relying on the directory |
| Before an interview | nothing more | `resolve --project ROOT --paths P... --modules M... --domains D... --symbols S...` |
| Writing a record | `references/adr-template.md` | `template`, then `propose` |
| After a verified merge | nothing more | `promote --adr ADR-NNNN --sha MERGED_SHA` |
| First use in a project | nothing more | `init-index --project ROOT` |

## Resolve: what governs this scope

Input: the paths, modules, domains and Codebase Map symbol identities the task
touches. Output: the `Accepted`, unsuperseded records that match, with the
reason for each match, most specific first. Load the one to three records that
matter into the interview or the worker brief; never the whole directory.
`Proposed` records are not returned: a decision not yet implemented binds only
the task that proposed it.

## Propose: the interview's output

Precondition: the interview fixed scope, at least one nominal, one boundary and
one rejection example, the alternatives it rejected and the invariants it
requires. Write the body from `template`, then run `propose` with title, slug,
the run or task identity, the current `HEAD`, the scope lists and any
`--supersedes`. The helper allocates the next identity, validates the sections
and refuses template placeholders. Outcome codes:

- `written`: the record exists as `Proposed` and the index lists it.
- `refused`: the helper named the missing section, item or scope; fix the body
  and run again. Do not hand-edit the index.

A record that supersedes another names it at proposal time, so reviewers can
compare the two while the task runs.

## Promote: at the merge, never before

Precondition: the candidate that implements the record is merged and the run's
required gates passed on that commit. `promote` sets `Accepted`,
`accepted_at_sha` and `last_verified_sha` to the merged commit, marks each
`supersedes` target `Superseded by` this record and rewrites the index, as one
transaction. A `Proposed` record that was abandoned stays `Proposed` with its
task identity; retire it by superseding it from a later record, never by
deletion.

## Instructions and documentation

Durable instructions (`AGENTS.md`, `CLAUDE.md`) carry the active records for a
domain inside the loop block that `project-knowledge:instructions-method`
maintains; the reasoning stays in the record. Guides cite a record by identity
and never restate its examples.
