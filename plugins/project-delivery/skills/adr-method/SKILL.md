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

Before choosing or revising alternatives, load `research:science-based-approach`
and compose its automatic checkpoint with the caller's run and grants. Cite
research identity, immutable revision and claim IDs with applicability and limits.
A changed source identifies decisions to review; it never rewrites or approves
an Accepted record. Reuse the same checkpoint when the interview already did it.

Once the interview fixed scope, nominal, boundary and rejection examples,
rejected alternatives and invariants, write the body and `propose` with
title, slug, run identity, `HEAD`, scope lists, any `--supersedes` (another
decision it replaces) and any `--depends-on` (`Accepted` decisions it builds
on). A refusal names what to fix; never hand-edit the index. To change an
`Accepted` decision, `propose --revise ADR-NNNN` writes its next version,
`Proposed` under the same number. `ADR-NNNN` cites the active version,
`ADR-NNNN vN` pins one.

Versions: at most one `Accepted` and one `Proposed` version per decision.

## Approve, retire, verify

`Accepted` means the user approved this exact text. Show the record with its `digest` (`validate --adr ADR-NNNN`) and ask. On
approval, `promote` sets `Accepted` and marks the previous version and each
`supersedes` target `Superseded`, as one transaction; record each
`dependents_to_review` as an open question (`ask`). Approval authorizes no
work; a merge never approves. Unapproved, a record stays `Proposed`;
abandoned, it gets `retire --adr ADR-NNNN --reason TEXT --expect-digest D`,
`Abandoned` for good. Never delete a record. A rewrite refuses, writing
nothing, on a digest other than `--expect-digest`: show the record again.

After a review confirms the code conforms, `verify` sets `last_verified_sha`;
approval never verifies. `validate --sha` lists as `drifted` each `Accepted`
record whose governed files changed since, `files: null` when never verified.

## Instructions and documentation

Durable instructions carry the active records for a domain inside the loop
block that `project-knowledge:instructions-method` maintains; guides cite a
record by identity and never restate its examples.
