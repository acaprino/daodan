---
description: >
  Realign the documentation with the code, or write what you ask for: a guide, the README, the project instructions.
  TRIGGER WHEN: the user asks for documentation, a guide, a README, onboarding docs, or project instructions (CLAUDE.md, AGENTS.md).
  DO NOT TRIGGER WHEN: the text only needs to sound natural (use /text-humanizer:humanize-text).
argument-hint: "[what to write]"
---

# Write the docs

$ARGUMENTS

Route the request above, then load the method it needs together with
`work-controller:work-record`:

| Request | Method |
|---|---|
| nothing, or "update the docs" | `project-knowledge:project-knowledge`: drift audit, then the authorized corrections |
| a guide, onboarding, architecture, flows, operations | `project-knowledge:project-knowledge`: its guide method |
| the README | `project-knowledge:readme-craft` |
| instructions, CLAUDE.md, AGENTS.md | `project-knowledge:instructions-method` |

Before anything is written, run `run_state.py first-use --project ROOT`; on
`first_use: true`, load `project-lifecycle:lifecycle-method` and follow its
`references/first-use.md` first.
Audit first; writing into the repository is an authorization asked when needed.
