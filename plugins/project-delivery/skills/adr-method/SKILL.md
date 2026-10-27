---
name: adr-method
description: >
  Create, resolve, validate, approve, version and verify canonical architecture decision records in docs/adr/.
  TRIGGER WHEN: the user explicitly asks to record or write down an architecture or technical decision, an interview settles a design, contract or domain decision, a task needs the decisions governing its scope, the user approves, revises or abandons a record, or a reviewed change verifies records or lists their drift.
  DO NOT TRIGGER WHEN: the user only wants brainstorming or advice without recording a decision, the change needs no decision beyond existing records, or the request is project documentation (use project-knowledge:project-knowledge).
---

# Architecture decision records

Load the skill `work-controller:work-record` for run ownership and authorization.
The helper is `python "${CLAUDE_PLUGIN_ROOT}/skills/adr-method/scripts/adr_tool.py"`;
it writes records and the index atomically and refuses an inconsistent state
first.

## Load map

| Step | Run |
|---|---|
| Any | `validate --project ROOT` before relying on records |
| Before an interview | `resolve --project ROOT --paths P... --modules M... --domains D... --symbols S...` |
| Writing a record or a version | read `references/adr-template.md`; `template`, then `propose` |
| The user approved the text shown | `promote --adr ADR-NNNN --sha HEAD_SHA --expect-digest D` |
| Code reviewed as conforming | `verify --adr ADR-NNNN --sha SHA --expect-digest D` |
| Status, realignment | `validate --project ROOT --sha HEAD_SHA` |
| First use in a project | `init-index --project ROOT` |

## Resolve: what governs this scope

Input: the paths, modules, domains and Codebase Map symbols the task touches.
Output: the `Accepted` version of each matching decision, its `digest` and why
it matches, most specific first. Load the one to three that matter, never the
whole directory.

## Propose: the interview's output

Before alternatives, load `research:science-based-approach` and compose its
automatic checkpoint. Cite research identity, immutable revision and claims with
applicability and limits. Changed sources identify reviews; they never rewrite
or approve Accepted records. Reuse an existing interview checkpoint.

After the interview fixes scope, examples, alternatives and invariants, write
the body and `propose` with title, slug, run identity, `HEAD`, scope lists and
optional `--supersedes`/`--depends-on`. A refusal names the fix; never hand-edit
the index. `propose --revise ADR-NNNN` writes the next `Proposed` version under
that number. `ADR-NNNN` cites the active version; `ADR-NNNN vN` pins one.

Versions: at most one `Accepted` and one `Proposed` version per decision.

## Approve, retire, verify

`Accepted` means the user approved this exact text. Show the record and digest,
then `promote`; previous and superseded versions change in one transaction.
Record `dependents_to_review` with `ask`. Approval authorizes no work or merge.
Unapproved records stay `Proposed`; abandon with
`retire --adr ADR-NNNN --reason TEXT --expect-digest D`; never delete.
A mismatched `--expect-digest` refuses the rewrite: show the record again.

After a review confirms the code conforms, `verify` sets `last_verified_sha`;
approval never verifies. `validate --sha` lists as `drifted` each `Accepted`
record whose governed files changed since, `files: null` when never verified.

## Instructions and documentation

Durable instructions carry the active records for a domain inside the loop
block that `project-knowledge:instructions-method` maintains; guides cite a
record by identity and never restate its examples.
