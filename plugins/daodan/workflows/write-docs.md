---
description: >
  Realign the documentation with the code, or write what you ask for: a guide, the README, the project instructions.
  TRIGGER WHEN: the user asks for documentation, a guide, a README, onboarding docs, or project instructions (CLAUDE.md, AGENTS.md).
  DO NOT TRIGGER WHEN: the text only needs to sound natural (use humanize-text).
argument-hint: "[what to write]"
---

# Write the docs

$ARGUMENTS

Load `project-delivery:delivery-method` and follow `references/document.md` to
coordinate evidence, scope, review and delivery. Route the request above to the
specialist method it needs together with `work-controller:work-record`:

| Request | Method |
|---|---|
| nothing, or "update the docs" | `project-knowledge:project-knowledge`: drift audit, then the authorized corrections |
| reorganize Daodan documentation, plugin dossiers, intake/provenance inventory | `project-knowledge:project-knowledge`: load `references/documentation-organization.md` and dispatch `project-knowledge:documentation-organizer` |
| a guide, onboarding, architecture, flows, operations | `project-knowledge:project-knowledge`: its guide method |
| the README | `project-knowledge:readme-craft` |
| instructions, CLAUDE.md, AGENTS.md | `project-knowledge:instructions-method` |

When instructions must list active records, load `project-delivery:adr-method`,
resolve them for the relevant domains and supply their identities, versions,
titles, scopes and digests to `project-knowledge:instructions-method`.

Before anything is written, run `run_state.py first-use --project ROOT`; on
`first_use: true`, load `project-delivery:delivery-method` and follow its
`references/first-use.md` first.
Audit first; writing into the repository is an authorization asked when needed.
Reuse an existing scoped authorization. For restructuring, the organizer's
forbidden `docs/superpowers/` output and per-document human retention/destination
decisions remain mandatory before the general writing authorization is applied.
